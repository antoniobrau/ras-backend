from datetime import datetime
from pydantic import BaseModel


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    email: str
    site: str | None = None
    level: str | None = None
    company: str | None = None
    active: bool
    created_at: datetime