from pydantic import BaseModel
from datetime import datetime

# 친구 신청 목록 조회
class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    requester_nickname: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True