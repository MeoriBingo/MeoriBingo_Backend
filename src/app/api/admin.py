from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

# 팀원들의 공용 설정 임포트
from src.app.core.database import get_db
from src.app.models.user import User

# 1. 라우터 설정 (main.py와 연결되는 통로)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# 2. 데이터 구조 정의 (Pydantic 모델)
class PointGrantRequest(BaseModel):
    amount: int       # 부여할 포인트 양
    reason: str      # 부여 사유

class PointHistory(BaseModel):
    timestamp: datetime
    amount: int
    reason: str
    status: str

class UserPointResponse(BaseModel):
    user_id: str
    current_total: int
    history: List[PointHistory]

# --- 임시 데이터 (DB 연결 전 테스트용으로 남겨두실 경우) ---
# 실제 DB를 사용한다면 이 부분은 나중에 삭제해도 됩니다.
user_data_mock = {} 

# 3. 포인트 부여 API (POST)
@router.post("/point/{user_id}")
async def grant_point(
    user_id: str, 
    request: PointGrantRequest, 
    db: Session = Depends(get_db)
):
    # [로직] DB에서 유저 찾기
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="존재하지 않는 사용자입니다."
        )
    
    # 포인트 추가
    user.point += request.amount
    
    try:
        db.commit()
        db.refresh(user)
        return {
            "message": f"{user_id}님에게 {request.amount} 포인트가 부여되었습니다.",
            "current_point": user.point,
            "reason": request.reason
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="DB 저장 중 오류 발생")

# 4. 포인트 내역 조회 API (GET)
@router.get("/point/{user_id}", response_model=UserPointResponse)
async def get_user_point_history(user_id: str, db: Session = Depends(get_db)):
    # [로직] DB에서 유저 조회
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    # 현재는 User 모델에 point만 있다면 아래처럼 반환합니다.
    # (실제 내역 리스트는 별도의 로그 테이블이 필요하지만, 우선 기본 틀을 맞췄습니다.)
    return UserPointResponse(
        user_id=user_id,
        current_total=user.point,
        history=[] # 내역 저장용 테이블이 완성되면 여기에 데이터를 채웁니다.
    )
