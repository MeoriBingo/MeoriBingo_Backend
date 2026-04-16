from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


class BingoCellDetail(BaseModel):
    position: int
    content: str
    is_marked: bool
    image_url: Optional[str] = None
    marked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BingoBoardHistory(BaseModel):
    id: int
    title: str
    created_at: datetime
    first_mission_cleared_at: Optional[datetime] = None
    one_line_cleared_at: Optional[datetime] = None
    two_lines_cleared_at: Optional[datetime] = None
    three_lines_cleared_at: Optional[datetime] = None
    all_cleared_at: Optional[datetime] = None
    cells: List[BingoCellDetail]

    class Config:
        from_attributes = True
