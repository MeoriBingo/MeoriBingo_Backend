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
    is_active: int

    class Config:
        from_attributes = True


# 미션 가이드 조회하기 (by. 서현)
class MissionGuideRead(BaseModel):
    guideText: str
    guideImage: Optional[str] = None
    tips: Optional[str] = None

    class Config:
        from_attributes = True
