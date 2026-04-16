from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    accessToken: str

class NicknameRequest(BaseModel):
    nickname: str