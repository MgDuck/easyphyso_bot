# core/entities/user.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class User(BaseModel):
    """Represents a user in the system."""
    id: Optional[int] = None  # Database ID, None if not yet persisted
    name: Optional[str] = None # Name from Telegram
    telegram_id: Optional[str] = None # Unique Telegram User ID
    balance: float = 0.0 # User's current balance
    created_at: Optional[datetime] = None # Timestamp of user creation
    updated_at: Optional[datetime] = None  # Timestamp of last update
    password_hash: Optional[str] = None  # Hashed password for HTTP API login
    api_key: Optional[str] = None  # API key for prediction endpoint

