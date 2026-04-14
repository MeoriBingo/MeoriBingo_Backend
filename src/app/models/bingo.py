from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    SmallInteger,
    DateTime,
    ForeignKey,
    func,
)
from src.app.core.database import Base


class BingoBoard(Base):
    __tablename__ = "bingo_board"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )  # PDF의 FOREIGN KEY
    mode = Column(String(255), nullable=False)  # NORMAL / CHALLENGE
    category = Column(String(255), nullable=True)
    status = Column(String(255), nullable=False)  # IN_PROGRESS 등
    completed_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class BingoCell(Base):
    __tablename__ = "bingo_cells"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    board_id = Column(BigInteger, ForeignKey("bingo_board.id"), nullable=False)
    mission_id = Column(BigInteger, ForeignKey("missions.id"), nullable=False)
    position = Column(SmallInteger, nullable=False)  # 1~9 위치
    status = Column(String(255), default="NONE", nullable=False)
    proof_image_url = Column(String(255), nullable=True)
    is_completed = Column(SmallInteger, default=0, nullable=False)
    completed_at = Column(DateTime, nullable=True)
