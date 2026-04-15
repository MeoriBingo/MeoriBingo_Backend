from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    provider: str
    accessToken: str

class NicknameRequest(BaseModel):
    nickname: str