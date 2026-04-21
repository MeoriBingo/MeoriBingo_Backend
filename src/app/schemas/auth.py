from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    authorizationCode: str


class NicknameRequest(BaseModel):
    nickname: str
