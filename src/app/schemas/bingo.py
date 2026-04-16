from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BingoGenerateRequest(BaseModel):
    user_id: int

class BingoCellBase(BaseModel):
    id: int
    mission_id: int
    position: int
    status: str
    is_completed: int

    class Config:
        from_attributes = True

class BingoBoardResponse(BaseModel):
    id: int
    user_id: int
    mode: str
    status: str
    completed_count: int
    cells: List[BingoCellBase]

    class Config:
        from_attributes = True
