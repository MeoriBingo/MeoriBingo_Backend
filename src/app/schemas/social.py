from pydantic import BaseModel
from datetime import datetime

# 친구 신청 목록 조회
class FriendRequestRead(BaseModel):
    id: int
    requester_id: int
    re
    created_at: datetime

    class Config:
        from_attributes = True


#친구 빙고판 반응 등록
class FriendBingoReactionRequest(BaseModel):
    id: int
    board_id: int
    reaction_type: str   # 예: "like", "clap", "heart"
