from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class BingoCellDetail(BaseModel):
    position: int
    mission_title: str  
    is_completed: bool  
    proof_image_url: Optional[str] = None  
    completed_at: Optional[datetime] = None  

    model_config = ConfigDict(from_attributes=True)


class BingoBoardHistory(BaseModel):
    id: int
    title: Optional[str] = None  
    created_at: datetime
    first_mission_cleared_at: Optional[datetime] = None
    one_line_cleared_at: Optional[datetime] = None
    two_lines_cleared_at: Optional[datetime] = None
    three_lines_cleared_at: Optional[datetime] = None
    all_cleared_at: Optional[datetime] = None
    cells: List[BingoCellDetail]

    model_config = ConfigDict(from_attributes=True)