from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# 공용 설정 및 모델 임포트
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.models.social import PointLog
from src.app.schemas.admin import PointGrantRequest, PointHistoryResponse

# 라우터 설정
router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/point/{user_id}")
async def grant_point_by_admin(
    user_id: int, 
    payload: PointGrantRequest, 
    db: Session = Depends(get_db)
):
    """
    관리자 권한으로 유저에게 포인트를 부여합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="유저를 찾을 수 없습니다."
        )

    # 1. 유저 포인트 업데이트
    user.point += payload.amount

    # 2. 포인트 내역 저장 (PointLog 테이블 활용)
    new_history = PointLog(
        user_id=user_id, 
        amount=payload.amount, 
        reason=payload.reason, 
        type="SAVED"
    )
    db.add(new_history)

    try:
        db.commit()
        db.refresh(user)
        return {
            "status": "success",
            "message": f"{user.nickname}님에게 {payload.amount}포인트가 부여되었습니다.",
            "current_point": user.point,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="DB 저장 중 오류 발생")


@router.get("/point/{user_id}", response_model=PointHistoryResponse)
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

    return {
        "status": "success", 
        "total_point": user.point, 
        "history": history
    }