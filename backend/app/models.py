"""SQLAlchemy models for the resume CMS prototype.

We define a simple `Resume` table that stores:
- id (primary key)
- filename (original uploaded name)
- content_json (JSONB/JSON column for parsed resume data)
- uploaded_at (timestamp)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_json = Column(JSON, nullable=False, default={})
    uploaded_at = Column(DateTime, default=datetime.utcnow)
