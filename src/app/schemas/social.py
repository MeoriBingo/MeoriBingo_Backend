from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FriendshipBase(BaseModel):
    requester_id: int
    addressee_id: int


class FriendshipCreate(FriendshipBase):
    pass

class FriendshipUpdate(BaseModel):
    user_id: int  # 액션을 수행하는 유저의 ID (addressee_id여야 함)
    status: str   # ACCEPTED 또는 REJECTED

class FriendshipRead(FriendshipBase):

    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
