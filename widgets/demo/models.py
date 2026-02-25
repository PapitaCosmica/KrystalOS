from sqlmodel import SQLModel, Field
from typing import Optional

class DemoItem(SQLModel, table=True):
    __tablename__ = "demo_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
