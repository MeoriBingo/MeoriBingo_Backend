from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.models.social import PointLog
from src.app.schemas.admin import PointGrantRequest, PointHistoryResponse

router = APIRouter()


@router.post("/{user_id}")
async def grant_point_by_admin(
    user_id: int, payload: PointGrantRequest, db: Session = Depends(get_db)
):
    """
    관리자 권한으로 유저에게 포인트를 부여합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 1. 유저 포인트 업데이트
    user.point += payload.amount

    # 2. 포인트 내역 저장
    new_history = PointLog(
        user_id=user_id, amount=payload.amount, reason=payload.reason, type="SAVED"
    )
    db.add(new_history)

    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "message": f"{user.nickname}님에게 {payload.amount}포인트가 부여되었습니다.",
        "current_point": user.point,
    }


@router.get("/{user_id}", response_model=PointHistoryResponse)
async def get_user_point_history(user_id: int, db: Session = Depends(get_db)):
    """
    유저의 포인트 적립 및 사용 내역을 조회합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    history = (
        db.query(PointLog)
        .filter(PointLog.user_id == user_id)
        .order_by(PointLog.created_at.desc())
        .all()
    )

    # 임시 목차 데이터 (DB 모델 없을 때 테스트용)
    history = []

    return {"status": "success", "total_point": user.point, "history": history}
