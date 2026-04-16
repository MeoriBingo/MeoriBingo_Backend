from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey, func
from src.app.core.database import Base
from datetime import datetime
from sqlalchemy.sql import func


class Friendship(Base):
    __tablename__ = "friendship"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    requester_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    addressee_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(String(255), nullable=False)  # PENDING, ACCEPTED
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PointLog(Base):
    __tablename__ = "point_log"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class BingoLike(Base):
    __tablename__ = "bingo_likes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    board_id = Column(BigInteger, ForeignKey("bingo_board.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reaction_type = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class BingoReaction(Base):
    __tablename__ = "bingo_reactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bingo_board_id = Column(Integer, ForeignKey("bingo_boards.id"))
    reaction_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
