from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

# 1. ReactionType
class ReactionType(str, Enum):
    HEART = "HEART"
    FIRE = "FIRE"
    LIKE = "LIKE"
    SMILE = "SMILE"
    BAD = "BAD"
    CRY = "CRY"

# --- 친구 관련 ---
class FriendshipBase(BaseModel):
    requester_id: int
    addressee_id: int

class FriendshipRead(FriendshipBase):
    id: int
    status: str

    class Config:
        from_attributes = True

class FriendshipCreate(FriendshipBase):
    pass

class FriendshipUpdate(BaseModel):
    user_id: int  
    status: str  # ACCEPTED 또는 REJECTED

class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    requester_nickname: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

        

# --- 빙고 현황/리스트 관련 ---

class FriendBingoStatus(BaseModel):
    user_id: int
    nickname: str
    profile_image: Optional[str] = None
    bingo_count: int
    progress_percentage: float
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class FriendListResponse(BaseModel):
    status: str
    message: str
    data: List[FriendBingoStatus]


class ReactionCreate(BaseModel):
    user_id: int
    bingo_board_id: int
    reaction_type: ReactionType 

class ReactionRead(BaseModel):
    id: int
    user_id: int
    reaction_type: ReactionType 
    created_at: datetime

    class Config:
        from_attributes = True

# --- 삭제 응답 ---
class FriendDeleteResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None 

    class Config:
        from_attributes = True