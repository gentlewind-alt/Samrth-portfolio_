from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel

class ResumeOut(BaseModel):
    id: int
    filename: str
    content_json: Dict[str, Any]
    uploaded_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
