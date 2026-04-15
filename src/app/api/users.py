from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.schemas.users import UserRead, UserUpdate, UserMissionUpdate

router = APIRouter(prefix="/users", tags=["Users"])


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
