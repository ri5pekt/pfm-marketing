from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class BusinessAccount(Base):
    __tablename__ = "business_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    meta_account_id = Column(String, nullable=True)
    meta_access_token = Column(String, nullable=True)  # Encrypted in production
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to rules
    rules = relationship("CampaignRule", back_populates="business_account", cascade="all, delete-orphan")


class CampaignRule(Base):
    __tablename__ = "campaign_rules"

    id = Column(Integer, primary_key=True, index=True)
    business_account_id = Column(Integer, ForeignKey("business_accounts.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    schedule_cron = Column(String, nullable=True)  # Cron expression (nullable for manual-only rules)
    conditions = Column(JSON, nullable=False)  # Rule conditions
    actions = Column(JSON, nullable=False)  # Actions to execute
    meta_account_id = Column(String, nullable=True)
    meta_access_token = Column(String, nullable=True)  # Encrypted in production
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to business account
    business_account = relationship("BusinessAccount", back_populates="rules")


class RuleLog(Base):
    __tablename__ = "rule_logs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False)  # success, error, skipped
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

