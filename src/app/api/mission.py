import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from azure.storage.blob import BlobServiceClient

# 모델 및 스키마 임포트
from src.app.core.database import get_db
from src.app.api import deps
from src.app.models.mission import Mission
from src.app.models.bingo import BingoCell, BingoBoard, BoardStatus, CellStatus
from src.app.models.user import User
from src.app.schemas.mission import (
    MissionVerifyResponse,
    MissionResponse,
    MissionGuideRead,
)
from src.app.service.BingoAIService import BingoAIService

router = APIRouter()
ai_service = BingoAIService() # AI 서비스 초기화

# Azure Storage 설정
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "mission-images")

def count_completed_lines(cells):
    done_pos = {c.position for c in cells if c.is_completed}
    win_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], 
        [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]
    ]
    return sum(1 for line in win_lines if all(pos in done_pos for pos in line))

@router.post("/verify/{cell_id}", response_model=MissionVerifyResponse)
async def picture_upload(
    cell_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise HTTPException(status_code=500, detail="Azure Storage 설정이 없습니다.")

    # 1. 파일 기본 체크
    allowed_extensions = [".jpg", ".jpeg", ".png"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    cell = db.query(BingoCell).filter(BingoCell.id == cell_id).first()
    if not cell:
        raise HTTPException(status_code=404, detail="해당 빙고 칸을 찾을 수 없습니다.")

    board = cell.board
    temp_file_path = f"temp_{uuid.uuid4()}{file_ext}"

    try:
        # 파일 내용을 메모리에 읽기
        contents = await file.read()
        
        # 2. AI 판독을 위해 임시 파일 저장
        with open(temp_file_path, "wb") as f:
            f.write(contents)

        # 3. AI 이미지 검증 실행 (BingoAIService 활용)
        # DB 세션과 미션 ID, 파일 경로를 전달합니다.
        verification_result = ai_service.verify_image_mission(db, cell.mission_id, temp_file_path)

        if verification_result != "SUCCESS":
            return MissionVerifyResponse(
                message=f"인증 실패: 사진에서 미션 목표를 확인할 수 없습니다. (결과: {verification_result})",
                image_url="",
                is_success=False
            )

        # 4. 검증 성공 시 Azure Blob Storage 업로드
        unique_filename = f"mission/user_{current_user.id}/{uuid.uuid4()}{file_ext}"
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=unique_filename)
        blob_client.upload_blob(contents, overwrite=True)
        image_url = blob_client.url

        # 5. 데이터 업데이트 및 포인트 지급 로직
        now = datetime.now()
        earned_points = 0
        
        cell.proof_image_url = image_url
        cell.is_completed = True
        cell.completed_at = now
        cell.status = CellStatus.DONE

        # 보드 상태 갱신
        board.completed_count = db.query(BingoCell).filter(
            BingoCell.board_id == board.id, 
            BingoCell.is_completed == True
        ).count()
        
        old_lines = board.completed_lines
        new_lines = count_completed_lines(board.cells)
        board.completed_lines = new_lines

        # 포인트 계산 (첫 미션, 줄 완성, 올클리어)
        if board.first_mission_cleared_at is None:
            board.first_mission_cleared_at = now
            earned_points += 100
        
        if new_lines >= 1 and board.one_line_cleared_at is None:
            board.one_line_cleared_at = now
            earned_points += 500
        # (기존의 2줄, 3줄 포인트 로직 동일하게 적용 가능)

        current_user.point += earned_points

        # 6. AI 축하 문구 생성 (BingoAIService 활용)
        # 빙고가 완성되었으면 lines를 전달하여 더 큰 축하를 보냅니다.
        ai_congrats_message = ai_service.request_openai(
            mission_obj=cell.mission, 
            lines=new_lines, 
            completed_at=now
        )

        db.commit()
        db.refresh(cell)

        return MissionVerifyResponse(
            message=ai_congrats_message, # AI가 생성한 맞춤형 문구
            image_url=image_url,
            is_success=True,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/missions", response_model=List[MissionResponse])  # 스키마 적용
async def get_missions(db: Session = Depends(get_db)):
    """
    DB에서 미션 목록을 전체 조회하여 반환합니다.
    """
    try:
        missions = db.query(Mission).all()
        return missions
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to upload to Azure or update DB: {str(e)}"
        )


# 미션 가이드 조회 서비스(by.서현)

@router.get("/{mission_id}/guide", response_model=MissionGuideRead)
def get_mission_guide(mission_id: int, db: Session = Depends(get_db)):
    """
    특정 미션 클릭시 "어떻게 찍으세요"라는 가이드 문구/이미지를 반환합니다.
    """

    # Mission 모델에서 mission_id로 데이터 조회
    my_mission_data = db.query(Mission).filter(Mission.id == mission_id).first()

    # 만약 찾는 미션이 없으면 에러 생성
    if my_mission_data is None:
        raise HTTPException(status_code=404, detail="해당 미션을 찾을 수 없습니다.")

    # MissionGuideRead에 잘 담아서 프론트로 전송
    return MissionGuideRead(
        guideText=f"[{my_mission_data.title}] {my_mission_data.description}",
        # guideImage=저희 가이드 이미지도 하기로 했었나욥...?
        # tips=(f"{my_mission_data.target_object}를 촬영하여 업로드하세요!"),
        ### tips에 'xxx'을 촬영하세요 일단 이런식으로 해두겠습니다
    )