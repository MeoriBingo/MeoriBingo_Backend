from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from src.app.core.database import get_db
from src.app.api import deps
from src.app.models.user import User
from src.app.models.bingo import BingoBoard, BingoCell, BoardStatus
from src.app.models.mission import Mission
from src.app.schemas.bingo import BingoGenerateRequest, BingoBoardResponse,ActiveBingoResponse,BingoCheckResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date, time
from src.app.service.BingoAIService import BingoAIService


router = APIRouter()
ai_service = BingoAIService()

@router.post("/generate", response_model=BingoBoardResponse)
async def generate_bingo_board(
    request: BingoGenerateRequest, db: Session = Depends(get_db)
):
    """
    새로운 빙고판을 생성합니다.
    1. bingo_board 테이블에 새로운 레코드 삽입
    2. missions 테이블에서 랜덤으로 9개 미션 선택
    3. bingo_cells 테이블에 9개 미션을 각 위치(1~9)에 배치
    """
    try:
        # 빙고판 생성
        new_board = BingoBoard(
            user_id=request.user_id,
            mode=request.mode.upper(),
            category=request.category,
            status="IN_PROGRESS",
            completed_count=0,
        )
        db.add(new_board)
        db.flush()  # board.id를 얻기 위해 flush 실행

        mode_param = request.mode.lower() if hasattr(request, 'mode') else "normal"
        category_param = request.category if hasattr(request, 'category') else "생산성"

        ai_missions = ai_service.generate_bingo_missions(
            mode=mode_param, 
            selected_category=category_param
        )

        if not ai_missions or len(ai_missions) < 9:
            raise HTTPException(
                status_code=500,
                detail="AI가 미션을 생성하지 못했습니다. 서비스 상태를 확인하세요.",
            )

        # 빙고 셀 생성
        bingo_cells = []
        for i, mission in enumerate(ai_missions):

            new_mission = Mission(
                title=mission.get('title', '제목 없음'),
                description=mission.get('description', ''),
                category=mission.get('category', category_param),
                is_active=1
            )
            db.add(new_mission)
            db.flush()

            new_cell = BingoCell(
                board_id=new_board.id,
                mission_id=new_mission.id,
                mission_title=new_mission.title,  
                category=new_mission.category,
                position=i + 1,  # 1~9
                status="IN_PROGRESS",
                is_completed=0,
            )
            db.add(new_cell)
            bingo_cells.append(new_cell)

        db.commit()
        db.refresh(new_board)

        # 응답 모델 구성을 위해 cells 추가 (Relationship이 모델에 정의되어 있지 않을 경우 대비)
        new_board.cells = bingo_cells
        return new_board

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Failed to generate bingo board: {str(e)}"
        )


@router.patch("/cells/{cell_id}")
async def update_bingo_cell_completion(cell_id: int, db: Session = Depends(get_db)):
    """
    특정 빙고 셀의 상태를 완료(COMPLETED)로 업데이트합니다.
    - status: 'COMPLETED'
    - is_completed: 1
    - completed_at: 현재 시간
    """
    cell = db.query(BingoCell).filter(BingoCell.id == cell_id).first()

    if not cell:
        raise HTTPException(status_code=404, detail="Bingo cell not found")

    try:
        cell.status = "COMPLETED"
        cell.is_completed = 1
        cell.completed_at = datetime.now()

        db.commit()
        db.refresh(cell)

        return {
            "message": "Bingo cell updated successfully",
            "cell_id": cell.id,
            "status": cell.status,
            "category": cell.mission.category,
            "is_completed": cell.is_completed,
            "completed_at": cell.completed_at,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update bingo cell: {str(e)}"
        )

@router.get("/active", response_model=ActiveBingoResponse)
def get_active_bingo(
    user_id: int, # 실제로는 인증 미들웨어를 통해 가져와야 합니다.
    db: Session = Depends(get_db)
):
    # 1. 사용자의 진행 중인 보드 조회 (셀 정보 포함)
    active_board = (
        db.query(BingoBoard)
        .options(joinedload(BingoBoard.cells)) # 관계 설정이 되어 있다고 가정
        .filter(
            BingoBoard.user_id == user_id,
            BingoBoard.status == "IN_PROGRESS"
        )
        .first()
    )

    if not active_board:
        raise HTTPException(status_code=404, detail="진행 중인 빙고판이 없습니다.")

    # 2. 데이터 반환 (Pydantic이 자동으로 매핑)
    return {
        "board_id": active_board.id,
        "mode": active_board.mode,
        "category": active_board.category,
        "completed_count": active_board.completed_count,
        "cells": active_board.cells 
    }
@router.get("/active/check", response_model=BingoCheckResponse)
def check_active_bingo(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """오늘 생성된 '진행 중'인 빙고판이 있는지 확인"""
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    active_board = db.query(BingoBoard).filter(
        BingoBoard.user_id == current_user.id,
        BingoBoard.status == BoardStatus.IN_PROGRESS,
        BingoBoard.created_at >= today_start,
        BingoBoard.created_at <= today_end
    ).first()

    return {
        "exists": active_board is not None,
        "board_id": active_board.id if active_board else None
    }

@router.post("/reset")
def reset_bingo_board(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """기존 판 보관 후 새 판 생성"""
    # 1. 기존에 진행 중이던 모든 판을 ARCHIVED로 변경
    db.query(BingoBoard).filter(
        BingoBoard.user_id == current_user.id,
        BingoBoard.status == BoardStatus.IN_PROGRESS
    ).update({"status": BoardStatus.ARCHIVED})
    
    # 2. 새로운 빙고판 생성 (기존에 만드신 생성 함수를 여기서 호출하세요)
    # new_board = create_new_bingo_logic(db, current_user.id)
    
    db.commit()
    return {"message": "Success", "detail": "Active board archived and new board created"}