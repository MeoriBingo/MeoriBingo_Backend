from sqlalchemy import Column, BigInteger, String, Integer, Date, DateTime, func
from src.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    social_provider = Column(String(255), nullable=False)
    social_id = Column(String(255), nullable=False)

    email = Column(String(255), nullable=True)

    nickname = Column(String(255), unique=True, nullable=False)
    profile_image_url = Column(String(255), nullable=True)

    point = Column(Integer, default=0, nullable=False)
    streak_count = Column(Integer, default=0, nullable=False)  # PDF의 STREAK CONUT

    last_completed_date = Column(Date, nullable=True)

    # 생성일시는 DB에서 자동으로 기록
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
