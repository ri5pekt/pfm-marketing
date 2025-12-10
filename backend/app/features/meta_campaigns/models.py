from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class AdAccount(Base):
    __tablename__ = "ad_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    meta_account_id = Column(String, nullable=True)
    meta_access_token = Column(String, nullable=True)  # Encrypted in production
    slack_webhook_url = Column(String, nullable=True)  # Slack webhook URL for notifications
    is_default = Column(Boolean, default=False)
    connection_status = Column(Boolean, nullable=True)  # True if connection is active, False if failed, None if not tested
    connection_last_checked = Column(DateTime(timezone=True), nullable=True)  # Last time connection was tested
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to rules
    rules = relationship("CampaignRule", back_populates="ad_account", cascade="all, delete-orphan")


class CampaignRule(Base):
    __tablename__ = "campaign_rules"

    id = Column(Integer, primary_key=True, index=True)
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, index=True)
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

    # Relationship to ad account
    ad_account = relationship("AdAccount", back_populates="rules")


class RuleLog(Base):
    __tablename__ = "rule_logs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False)  # success, error, skipped
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

