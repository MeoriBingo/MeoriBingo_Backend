from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/point/{user_id}")
async def grant_point(...):



###### 포인트 부여 ######


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



###### 포인트 내역 조회 ######

## 1 . 내역 저장을 위한 데이터 구조 설계(조회 기능을 만들기 위해, 먼저 포인트를 부여할 때마다 기록 저장)

from pydantic import BaseModel
from datetime import datetime
from typing import List

# 1. 내역 한 줄에 들어갈 정보 정의
class PointHistory(BaseModel):
    timestamp: datetime  # 언제
    amount: int         # 얼마를 (양수는 적립, 음수는 사용)
    reason: str        # 왜
    status: str        # 적립/사용 구분

# 2. 여러 개의 내역을 담을 응답 형식
class UserPointResponse(BaseModel):
    user_id: str
    current_total: int
    history: List[PointHistory]


## 2. 포인트 부여 시 기록 남기기 [POST 수정] (조회 기능을 만들기 위해, 앞서 만든 grant_point 함수가 실행될 때마다 내역 리스트에 데이터를 추가하도록 코드를 보완)

# 가상의 DB (메모리에 저장)
user_data = {
    "user123": {
        "total": 100,
        "history": []
    }
}

@app.post("/api/admin/point/{user_id}")
async def grant_point(user_id: str, request: PointGrantRequest):
    if user_id not in user_data:
        # 새로운 유저라면 초기화
        user_data[user_id] = {"total": 0, "history": []}
    
    # 1. 포인트 계산
    user_data[user_id]["total"] += request.amount
    
    # 2. 내역 기록 추가 (이 부분이 중요!)
    new_history = PointHistory(
        timestamp=datetime.now(),
        amount=request.amount,
        reason=request.reason,
        status="적립" if request.amount > 0 else "사용"
    )
    user_data[user_id]["history"].append(new_history)
    
    return {"message": "포인트 부여 및 내역 기록 완료"}


## 3. 포인트 내역 조회 API 만들기 [GET] (명세서에 있던 api/admin/point/{user_id} 기능 구현)

@app.get("/api/admin/point/{user_id}", response_model=UserPointResponse)
async def get_user_point_history(user_id: str):
    if user_id not in user_data:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    return UserPointResponse(
        user_id=user_id,
        current_total=user_data[user_id]["total"],
        history=user_data[user_id]["history"]
    )

