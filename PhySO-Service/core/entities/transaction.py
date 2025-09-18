# core/entities/transaction.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    """Represents a financial transaction for a user."""
    id: int | None = None # Database ID
    user_id: int | None = None # Foreign key to User
    amount: float = 0.0 # Positive for deposit, negative for withdrawal/charge
    description: str | None = None # Optional description (e.g., "Prediction cost", "Balance top-up")
    prediction_id: int | None = None # Optional foreign key to Prediction if charge is for a specific prediction
    created_at: datetime | None = None # Timestamp of the transaction
