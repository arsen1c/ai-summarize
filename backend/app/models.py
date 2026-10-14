from sqlalchemy import Column, Integer, Text, String, DateTime
from sqlalchemy.sql import func

from .database import Base


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON-encoded list of 3 strings
    status = Column(String, nullable=False, default="completed")  # completed | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
