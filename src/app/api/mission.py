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

router = APIRouter()

# Azure Storage 설정
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "mission-images")


# 현재 완성된 빙고 줄 수를 계산
def count_completed_lines(cells):
    done_pos = {c.position for c in cells if c.is_completed}
    win_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # 가로
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # 세로
        [0, 4, 8], [2, 4, 6]             # 대각선
    ]
    return sum(1 for line in win_lines if all(pos in done_pos for pos in line))


@router.post("/verify/{cell_id}", response_model=MissionVerifyResponse)
async def picture_upload(
    cell_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user) # 포인트 지급을 위해 유저 정보 필요
):
    """
    미션 사진을 Azure Storage에 업로드하고 bingo_cells 테이블의 proof_image_url을 업데이트합니다.
    - 파일 이름을 고유하게 생성하여 업로드
    - 업로드된 사진의 URL을 DB에 저장
    """
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise HTTPException(
            status_code=500, detail="Azure Storage connection string is not configured"
        )

    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    # DB에서 해당 셀 확인
    cell = db.query(BingoCell).filter(BingoCell.id == cell_id).first()
    if not cell:
        raise HTTPException(status_code=404, detail="Bingo cell not found")

    board = cell.board

    try:
        unique_filename = f"mission/user_id/{uuid.uuid4()}{file_ext}"
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_CONTAINER_NAME, blob=unique_filename
        )
        contents = await file.read()
        blob_client.upload_blob(contents, overwrite=True)

        # 업로드된 파일의 URL
        image_url = blob_client.url

        # --- 데이터 업데이트 및 포인트 로직 시작 ---
        now = datetime.now()
        earned_points = 0
        
        # 1. 셀 상태 업데이트
        cell.proof_image_url = image_url
        cell.is_completed = True
        cell.completed_at = now
        cell.status = CellStatus.DONE

        # 2. 보드 완료 개수 갱신
        current_done_count = db.query(BingoCell).filter(
            BingoCell.board_id == board.id, 
            BingoCell.is_completed == True
        ).count()
        board.completed_count = current_done_count

        board.completed_lines = count_completed_lines(board.cells)

        # 3. 포인트 판정 (중복 지급 방지)
        # [첫 미션 달성]
        if board.first_mission_cleared_at is None:
            board.first_mission_cleared_at = now
            earned_points += 100

        # [줄 완성 체크]
        total_lines = count_completed_lines(board.cells)
        if total_lines >= 1 and board.one_line_cleared_at is None:
            board.one_line_cleared_at = now
            earned_points += 500
        if total_lines >= 2 and board.two_lines_cleared_at is None:
            board.two_lines_cleared_at = now
            earned_points += 1000
        if total_lines >= 3 and board.three_lines_cleared_at is None:
            board.three_lines_cleared_at = now
            earned_points += 2000

        # [올 클리어]
        if board.completed_count == 9 and board.all_cleared_at is None:
            board.all_cleared_at = now
            board.status = BoardStatus.COMPLETED
            earned_points += 5000

        # 4. 유저 포인트 반영
        current_user.point += earned_points
        # ---------------------------------------

        # DB 저장
        db.commit()
        db.refresh(cell)

        return MissionVerifyResponse(
            message=f"Successfully uploaded and updated database. Earned {earned_points}pt!",
            image_url=image_url,
            is_success=True,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to upload to Azure: {str(e)}"
        )


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