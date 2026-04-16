from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    DateTime,
    Date,
    index,
)
from sqlalchemy.orm import relationship
from src.app.core.database import Base
from datetime import datetime


class BingoBoard(Base):
    __tablename__ = "bingo_boards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)

    # 해당 빙고판이 생성된 날짜 (과거 기록 조회용)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 달성 기록 히스토리
    first_mission_cleared_at = Column(DateTime, nullable=True)
    one_line_cleared_at = Column(DateTime, nullable=True)
    two_lines_cleared_at = Column(DateTime, nullable=True)
    three_lines_cleared_at = Column(DateTime, nullable=True)
    all_cleared_at = Column(DateTime, nullable=True)

    cells = relationship(
        "BingoCell", back_populates="board", order_by="BingoCell.position"
    )


class BingoCell(Base):
    __tablename__ = "bingo_cells"
    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("bingo_boards.id"))
    content = Column(String)
    image_url = Column(String, nullable=True)
    is_marked = Column(Boolean, default=False)
    marked_at = Column(DateTime, nullable=True)
    position = Column(Integer)  # 0~8

    board = relationship("BingoBoard", back_populates="cells")
