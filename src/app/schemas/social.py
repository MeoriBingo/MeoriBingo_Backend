from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 친구 신청 목록 조회 (신청한 사람의 정보를 포함하는 것이 좋습니다)
class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    requester_nickname: Optional[str] = None  # 화면에 표시할 닉네임 추가
    status: str  # PENDING, ACCEPTED 등 상태값
    created_at: datetime

    class Config:
        from_attributes = True

# 친구 빙고 현황 조회
class FriendBingoStatus(BaseModel):
    user_id: int
    nickname: str
    profile_image: Optional[str] = None
    bingo_count: int  # 완성된 빙고 줄 수
    progress_percentage: float  # 전체 칸 대비 채워진 비율 (0.0 ~ 100.0)
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True

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