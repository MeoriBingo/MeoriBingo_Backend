from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.app.core.database import get_db
from src.app.models.bingo import BingoBoard
from src.app.models.user import User
from src.app.api import deps
from datetime import date, datetime, timedelta
from typing import List
from src.app.schemas.bingo_detail import BingoBoardHistory

# ... router 설정 ...

router = APIRouter()


@router.get("/history/by-date", response_model=List[BingoBoardHistory])
def get_bingo_history_by_date(
    target_date: date = Query(..., description="조회하고 싶은 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    특정 날짜에 생성된 나의 빙고 기록(상세 상태 및 달성 시간 포함)을 조회합니다.
    """
    # 해당 날짜의 시작과 끝 범위 설정 (00:00:00 ~ 23:59:59)
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    # 해당 날짜 범위에 생성된 현재 사용자의 빙고판 조회
    histories = (
        db.query(BingoBoard)
        .filter(
            BingoBoard.user_id == current_user.id,
            BingoBoard.created_at >= start_dt,
            BingoBoard.created_at <= end_dt,
        )
        .all()
    )

    if not histories:
        return (
            []
        )  # 혹은 404를 내뱉을 수 있지만, 기록이 없는 날은 빈 리스트가 자연스럽습니다.

    return histories


@router.get("/history/monthly", response_model=List[BingoBoardHistory])
def get_monthly_bingo_summary(
    year: int = Query(..., ge=2024),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # 해당 월의 시작일과 다음 달 시작일 계산
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    histories = (
        db.query(BingoBoard)
        .filter(
            BingoBoard.user_id == current_user.id,
            BingoBoard.created_at >= start_date,
            BingoBoard.created_at < end_date, # 다음 달 1일 미만까지
        )
        .all()
    )
    return histories