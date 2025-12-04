from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Time, Text
from sqlalchemy.sql import func
from app.core.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    feature = Column(String, nullable=False, index=True)
    status = Column(String, default="pending")  # pending, running, done, error
    input_filename = Column(String, nullable=True)
    output_filename = Column(String, nullable=True)
    options = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScheduledExport(Base):
    __tablename__ = "scheduled_exports"

    id = Column(Integer, primary_key=True, index=True)
    feature = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    period = Column(String, nullable=False)  # minute, daily, weekly, monthly
    frequency = Column(Integer, nullable=False)
    time = Column(Time, nullable=True)
    day_of_week = Column(Integer, nullable=True)  # 0-6
    day_of_month = Column(Integer, nullable=True)  # 1-31
    timezone = Column(String, default="UTC")
    enabled = Column(Boolean, default=True)
    rq_job_id = Column(String, nullable=True)
    options = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

