from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    DateTime,
    ForeignKey,
    func,
    Enum as SQLEnum,
)
from src.app.core.database import Base
from datetime import datetime
from sqlalchemy.sql import func
import enum


class ReactionType(str, enum.Enum):
    HEART = "HEART"
    FIRE = "FIRE"
    LIKE = "LIKE"
    SMILE = "SMILE"
    BAD = "BAD"
    CRY = "CRY"


class FriendStatus(str, enum.Enum):
    PENDING = "PENDING"  # 요청 대기
    ACCEPTED = "ACCEPTED"  # 친구 수락
    REJECTED = "REJECTED"  # 요청 거절


class Friendship(Base):
    __tablename__ = "friendship"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    requester_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    addressee_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(FriendStatus), default=FriendStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PointLog(Base):
    __tablename__ = "point_log"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    point_type = Column(String(255), nullable=False) 
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

class BingoReaction(Base):
    __tablename__ = "bingo_reactions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    bingo_board_id = Column(BigInteger, ForeignKey("bingo_board.id"), nullable=False)
    reaction_type = Column(SQLEnum(ReactionType), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
