from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntryCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v


class EntryOut(BaseModel):
    id: int
    original_text: str
    summary: Optional[str]
    tags: List[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIOutput(BaseModel):
    summary: str
    tags: List[str] = Field(..., min_length=3, max_length=3)
