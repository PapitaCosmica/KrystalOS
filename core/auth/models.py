from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class DocumentBase(SQLModel):
    name: str

# In a real app, this would be imported from core/database.py
class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    permissions: str = Field(default="*") # Could be JSON or comma-separated string

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    role: Optional[Role] = Relationship()
    
    # A11y Preferences (Phase 5 integration)
    prefers_high_contrast: bool = False
    prefers_reduced_motion: bool = False
    prefers_large_text: bool = False
