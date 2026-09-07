from sqlmodel import SQLModel, Field
from typing import Optional

class Users(SQLModel, table=True):

    user_id: str | None = Field(
        default=None,
        primary_key=True
    )

    user_password: str
    user_name: str
    user_email: str
    user_phone: str
    user_addr: str
    user_warning_count: int
    user_status: str