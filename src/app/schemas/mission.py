from pydantic import BaseModel
from typing import Optional


class MissionVerifyResponse(BaseModel):
    message: str
    image_url: str
    is_success: bool = True
