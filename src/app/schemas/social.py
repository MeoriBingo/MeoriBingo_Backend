from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# 1. 친구 신청 목록 조회
class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    requester_nickname: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# 2. 친구 한 명의 상세 정보 (빙고 현황 포함)
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

    class Config:
        from_attributes = True

# 친구 삭제 성공 시 응답 모델
class FriendDeleteResponse(BaseModel):
    status: str
    message: str
    data: dict 

    class Config:
        from_attributes = True