from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.types import JSON
from app.database.session import Base

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)    
    participant_info = Column(JSON)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    responses = Column(MutableList.as_mutable(JSON), default=list)
    test_config = Column(JSON)
    statistics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
