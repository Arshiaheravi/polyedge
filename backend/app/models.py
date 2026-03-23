from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    subscription_tier = Column(String, default="free")  # free / basic / vip
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    telegram_verified = Column(Boolean, default=False)
    telegram_verify_code = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    follows = relationship("BettorFollow", back_populates="user", cascade="all, delete-orphan")
    alert_setting = relationship("AlertSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")


class BettorFollow(Base):
    __tablename__ = "bettor_follows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bettor_address = Column(String, nullable=False, index=True)
    bettor_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="follows")


class AlertSetting(Base):
    __tablename__ = "alert_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    web_push_enabled = Column(Boolean, default=False)
    telegram_enabled = Column(Boolean, default=False)
    push_subscription = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alert_setting")


class BetEvent(Base):
    __tablename__ = "bet_events"

    id = Column(Integer, primary_key=True, index=True)
    bettor_address = Column(String, nullable=False, index=True)
    market_id = Column(String, nullable=True)
    market_question = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)
    amount_usd = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
