from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    nickname: str
    point: int = 0
    streak_count: int = 0
    last_completed_date: Optional[date] = None


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_image_url: Optional[str] = None


class UserMissionUpdate(BaseModel):
    streak_count: Optional[int] = None
    last_completed_date: Optional[date] = None
    
class WeeklyStat(BaseModel):
    date: date
    count: int

class CategoryStat(BaseModel):
    category: str
    count: int
    percentage: float

class UserStatsResponse(BaseModel):
    status: str
    data: dict

    class Config:
        from_attributes = True