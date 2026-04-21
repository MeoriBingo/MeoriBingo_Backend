from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class BingoGenerateRequest(BaseModel):
    user_id: int
    mode: str
    category: Optional[str]

    class Config:
        from_attributes = True

class BingoCellSchema(BaseModel):
    id: int
    mission_id: int
    mission_title: str  # 추가됨
    position: int
    category: str
    status: str
    proof_image_url: Optional[str] = None
    is_completed: bool # int를 bool로 자동 변환하게 설정하면 좋습니다.

    class Config:
        from_attributes = True

class BingoBoardResponse(BaseModel):
    id: int
    user_id: int
    mode: str
    category: Optional[str]
    status: str
    completed_count: int
    cells: List[BingoCellSchema]

    class Config:
        from_attributes = True

class ActiveBingoResponse(BaseModel):
    board_id: int
    mode: str
    category: Optional[str]
    completed_count: int
    cells: List[BingoCellSchema]

    class Config:
        from_attributes = True
        
class BingoCheckResponse(BaseModel):
    exists: bool
    board_id: Optional[int] = None