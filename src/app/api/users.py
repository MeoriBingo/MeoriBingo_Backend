from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List

from src.app.core.database import get_db
from src.app.api import deps
from src.app.models.user import User
from src.app.models.bingo import BingoBoard, BingoCell
from src.app.models.mission import Mission
from src.app.schemas.users import (
    UserRead,
    UserUpdate,
    UserMissionUpdate,
    UserStatsResponse,
)

router = APIRouter()


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 정보를 조회합니다.
    조회 항목: email, nickname, point, streak_count, last_completed_date
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me/{user_id}", response_model=UserRead)
async def update_user_profile(
    user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)
):
    """
    사용자의 프로필(nickname, email, profile_image_url)을 업데이트합니다.
    값이 제공된 필드만 변경하며, nickname 중복 여부를 확인합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # model_dump를 통해 user_update 객체를 딕셔너리형태로 변환
    # exclude_unset=True: 변경된 값이 있는 부분만 추출
    update_data = user_update.model_dump(exclude_unset=True)

    # nickname 중복 확인 (본인이 아닌 다른 사용자가 이미 사용 중인 경우)
    if "nickname" in update_data:
        existing_user = (
            db.query(User)
            .filter(User.nickname == update_data["nickname"], User.id != user_id)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="존재하는 닉네임 입니다.")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.patch("/mission/{user_id}", response_model=UserRead)
async def update_user_mission(
    user_id: int, user_mission_update: UserMissionUpdate, db: Session = Depends(get_db)
):
    """
    사용자의 미션 정보(streak_count, last_completed_date)를 업데이트합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # model_dump를 통해 user_mission_update 객체를 딕셔너리형태로 변환
    # exclude_unset=True: 변경된 값이 있는 부분만 추출
    user_mission_update_data = user_mission_update.model_dump(exclude_unset=True)

    for field, value in user_mission_update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.get("/me/stats", response_model=UserStatsResponse)
def get_user_stats(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)
):
    # 1. 날짜 설정 (최근 7일 - 오늘 포함)
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    # 2. 주간 성취 데이터 (날짜별 완료 개수)
    # BingoCell에서 해당 유저의 보드에 속한 셀들을 가져옴
    weekly_raw = (
        db.query(
            func.date(BingoCell.completed_at).label("date"),
            func.count(BingoCell.id).label("count"),
        )
        .join(BingoBoard, BingoCell.board_id == BingoBoard.id)
        .filter(
            BingoBoard.user_id == current_user.id,
            BingoCell.is_completed == 1,
            func.date(BingoCell.completed_at) >= seven_days_ago,
        )
        .group_by(func.date(BingoCell.completed_at))
        .all()
    )

    # 빈 날짜 채워주기 (그래프 끊김 방지)
    weekly_dict = {r.date: r.count for r in weekly_raw}
    weekly_stats = [
        {
            "date": seven_days_ago + timedelta(days=i),
            "count": weekly_dict.get(seven_days_ago + timedelta(days=i), 0),
        }
        for i in range(7)
    ]

    # 3. 카테고리별 데이터 (전체 기간 기준)
    category_raw = (
        db.query(Mission.category, func.count(BingoCell.id).label("count"))
        .join(BingoCell, Mission.id == BingoCell.mission_id)
        .join(BingoBoard, BingoCell.board_id == BingoBoard.id)
        .filter(BingoBoard.user_id == current_user.id, BingoCell.is_completed == 1)
        .group_by(Mission.category)
        .all()
    )

    total_count = sum(c.count for c in category_raw)
    category_stats = [
        {
            "category": c.category,
            "count": c.count,
            "percentage": (
                round((c.count / total_count * 100), 1) if total_count > 0 else 0
            ),
        }
        for c in category_raw
    ]

    return {
        "status": "success",
        "data": {
            "nickname": current_user.nickname,
            "streak_count": current_user.streak_count,
            "weekly_stats": weekly_stats,
            "category_stats": category_stats,
        },
    }
