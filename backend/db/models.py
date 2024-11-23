from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class journal_entry(BaseModel):
    id: UUID
    user_id: UUID
    entry: str
    created_at: datetime

class journal_analysis(BaseModel):
    id: UUID
    entry_id: UUID
    mood: str
    summary: str
    created_at: datetime