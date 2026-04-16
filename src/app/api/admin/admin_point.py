from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.models.user import User

# [중요] 이 줄이 있어야 main.py와 연결 가능
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# 예시: 포인트 부여 API (DB 연결 버전)
@router.post("/point/{user_id}")
async def grant_point(
    user_id: str, 
    request: PointGrantRequest, 
    db: Session = Depends(get_db) # DB 세션을 자동으로 가져옵니다.
):
    # 이제 여기서 db를 이용해 유저를 찾고 포인트를 업데이트할 수 있어요!
    pass

## 1. 포인트 부여를 위한 '데이터 틀' 만들기(관리자가 서버에서 유저에게 포인트 부여)

from pydantic import BaseModel

# 포인트를 부여할 때 필요한 정보 정의
class PointGrantRequest(BaseModel):
    amount: int       # 부여할 포인트 양
    reason: str      # 부여 사유 (예: "미션 성공 인증", "이벤트 참여")


## 2. 포인트 부여 API 로직 (FastAPI)
from fastapi import FastAPI, HTTPException

app = FastAPI()

# 임시 데이터베이스 역할을 하는 리스트 (실제로는 Azure DB와 연결될 부분)
user_points_db = {
    "user123": 100,
    "user456": 50
}

@app.post("/api/admin/point/{user_id}")
async def grant_point(user_id: str, request: PointGrantRequest):
    # 1. 유저가 존재하는지 확인
    if user_id not in user_points_db:
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")
    
    # 2. 포인트 추가 로직
    old_point = user_points_db[user_id]
    new_point = old_point + request.amount
    user_points_db[user_id] = new_point
    
    # 3. 결과 반환
    return {
        "message": f"{user_id}님에게 {request.amount} 포인트가 부여되었습니다.",
        "previous_point": old_point,
        "current_point": new_point,
        "reason": request.reason
    }



