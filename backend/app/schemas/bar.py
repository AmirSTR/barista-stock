from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BarBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the coffee bar / location")
    telegram_chat_id: Optional[int] = Field(None, description="Telegram chat ID for notifications and orders")
    is_active: bool = Field(True, description="Whether the bar is active")


class BarCreate(BarBase):
    pass


class BarUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    telegram_chat_id: Optional[int] = None
    is_active: Optional[bool] = None


class BarResponse(BarBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
