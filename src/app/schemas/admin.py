from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# 포인트 부여 요청용
class PointGrantRequest(BaseModel):
    amount: int
    reason: str


# 포인트 내역 응답용
class PointHistoryRead(BaseModel):
    id: int
    amount: int
    reason: str
    type: str  # SAVED (적립) / USED (사용)
    created_at: datetime

    class Config:
        from_attributes = True


class PointHistoryResponse(BaseModel):
    status: str
    total_point: int
    history: List[PointHistoryRead]
