from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class FriendshipBase(BaseModel):
    requester_id: int
    addressee_id: int


class FriendshipCreate(FriendshipBase):
    pass


class FriendshipUpdate(BaseModel):
    user_id: int  # 액션을 수행하는 유저의 ID (addressee_id여야 함)
    status: str  # ACCEPTED 또는 REJECTED


class FriendshipRead(FriendshipBase):

    id: int
    status: str


# 친구 신청 목록 조회 (신청한 사람의 정보를 포함하는 것이 좋습니다)
class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    requester_nickname: Optional[str] = None  # 화면에 표시할 닉네임 추가
    status: str  # PENDING, ACCEPTED 등 상태값
    created_at: datetime

    class Config:
        from_attributes = True


# 1. 친구 신청 목록 조회
class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    requester_nickname: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# 친구 빙고 현황 조회
class FriendBingoStatus(BaseModel):
    user_id: int
    nickname: str
    profile_image: Optional[str] = None
    bingo_count: int  # 완성된 빙고 줄 수
    progress_percentage: float
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


# 3. 친구 목록 전체 응답 모델 수정
class FriendListResponse(BaseModel):
    status: str
    message: str
    data: List[FriendBingoStatus] 

#친구 빙고 반응 (by지우)
#보낼 때
class ReactionCreate(BaseModel):
    id: int
    user_id: int
    bingo_board_id: int
    reaction_type: str 

# 보여줄  때
class ReactionRead(BaseModel):
    id: int
    user_id: int
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True

# 친구 목록 조회 - 친구 한 명
class FriendItem(BaseModel):
    id: int
    nickname: str
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True

# 친구 삭제 성공 시 응답 모델
class FriendDeleteResponse(BaseModel):
    status: str
    message: str
    data: dict 

    class Config:
        from_attributes = True
    data: List[FriendItem]
