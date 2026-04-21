from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class BingoCellDetail(BaseModel):
    id: int
    position: int
    mission_title: Optional[str] = "알 수 없는 미션"
    is_completed: bool
    proof_image_url: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BingoBoardHistory(BaseModel):
    id: int
    title: Optional[str] = "이름 없는 빙고판"
    created_at: datetime
    first_mission_cleared_at: Optional[datetime] = None
    one_line_cleared_at: Optional[datetime] = None
    two_lines_cleared_at: Optional[datetime] = None
    three_lines_cleared_at: Optional[datetime] = None
    all_cleared_at: Optional[datetime] = None
    cells: List[BingoCellDetail]

    model_config = ConfigDict(from_attributes=True)
