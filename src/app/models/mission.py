from sqlalchemy import Column, BigInteger, String, Text, Integer, SmallInteger
from src.app.core.database import Base


class Mission(Base):
    __tablename__ = "missions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=False)
    difficulty = Column(SmallInteger, nullable=False)
    target_object = Column(String(255), nullable=True)
    is_active = Column(SmallInteger, default=1, nullable=False)
