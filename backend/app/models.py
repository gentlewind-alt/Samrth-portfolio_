"""Database models for resume and portfolio data."""
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Resume(Base):
    """Resume model storing PDF metadata and parsed content."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    filepath = Column(String, unique=True)
    content_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SlapCount(Base):
    """Track Chiyo slap interactions."""
    __tablename__ = "slap_counts"

    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Config(Base):
    """Store portfolio configuration."""
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, index=True)
    active_resume_id = Column(Integer, default=None)
    portfolio_title = Column(String, default="Portfolio")
    portfolio_theme = Column(String, default="light")
    config_data = Column(JSON, default={})
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
