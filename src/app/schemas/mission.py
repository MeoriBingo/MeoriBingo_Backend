from pydantic import BaseModel
from typing import Optional


class MissionVerifyResponse(BaseModel):
    message: str
    image_url: str
    is_success: bool = True

class MissionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    difficulty: int
    target_object: Optional[str] = None
    is_active: int

    class Config:
        from_attributes = True
