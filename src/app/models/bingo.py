from sqlalchemy import (
    Column, BigInteger, String, Integer, SmallInteger, 
    DateTime, ForeignKey, func, Boolean
)
from src.app.core.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class BingoBoard(Base):
    __tablename__ = "bingo_board" 

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # 설정 정보
    title = Column(String(255), nullable=True) 
    mode = Column(String(255), nullable=False)  # NORMAL / CHALLENGE
    category = Column(String(255), nullable=True)
    status = Column(String(255), nullable=False)  # IN_PROGRESS, COMPLETED 등
    
    # 달성 기록 (통계용 필드 통합)
    completed_count = Column(Integer, default=0, nullable=False)
    first_mission_cleared_at = Column(DateTime, nullable=True)
    one_line_cleared_at = Column(DateTime, nullable=True)
    two_lines_cleared_at = Column(DateTime, nullable=True)
    three_lines_cleared_at = Column(DateTime, nullable=True)
    all_cleared_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # 관계 설정 (back_populates가 더 명시적이라 추천합니다)
    cells = relationship("BingoCell", back_populates="board", order_by="BingoCell.position", cascade="all, delete-orphan")


class BingoCell(Base):
    __tablename__ = "bingo_cells"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    board_id = Column(BigInteger, ForeignKey("bingo_board.id"), nullable=False)
    mission_id = Column(BigInteger, ForeignKey("missions.id"), nullable=False)
    
    # 미션 정보 
    mission_title = Column(String(255), nullable=False)
    position = Column(SmallInteger, nullable=False)  # 0~8 또는 1~9 
    
    # 상태 및 인증
    status = Column(String(255), default="NONE", nullable=False) # NONE, PENDING, DONE
    proof_image_url = Column(String(255), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # 관계 설정
    board = relationship("BingoBoard", back_populates="cells")
    mission = relationship("Mission")