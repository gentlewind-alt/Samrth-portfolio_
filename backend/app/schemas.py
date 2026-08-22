"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContentSection(BaseModel):
    """Single content section with headline and body."""
    headline: str = ""
    body: str = ""


class ResumeContent(BaseModel):
    """Parsed resume content structure."""
    name: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    number: Optional[str] = None
    links: List[str] = []
    description: ContentSection = Field(default_factory=ContentSection)
    experience: ContentSection = Field(default_factory=ContentSection)
    project: ContentSection = Field(default_factory=ContentSection)
    education: ContentSection = Field(default_factory=ContentSection)
    skills: ContentSection = Field(default_factory=ContentSection)
    strengths: ContentSection = Field(default_factory=ContentSection)
    hobbies: ContentSection = Field(default_factory=ContentSection)
    status: ContentSection = Field(default_factory=ContentSection)
    focus: ContentSection = Field(default_factory=ContentSection)
    availability: ContentSection = Field(default_factory=ContentSection)


class ResumeOut(BaseModel):
    """Resume response schema."""
    id: int
    filename: str
    content_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeList(BaseModel):
    """List of resumes."""
    resumes: List[ResumeOut]
    total: int


class AdminRequest(BaseModel):
    """Request to update resume content."""
    content_json: Dict[str, Any]


class PortfolioMetadata(BaseModel):
    """Portfolio metadata."""
    title: str
    theme: str
    activeResumeId: Optional[int] = None
