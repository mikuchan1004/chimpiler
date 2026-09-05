from sqlmodel import SQLModel, Field
from typing import Optional

class users(SQLModel, table=True):

    user_id: str | None = Field(
        default=None,
        primary_key=True
    )

    user_password: str
    user_name: str
    user_phone: int = None
    user_addr: str
    user_warning_count: int
    user_status: str
    user_email: str