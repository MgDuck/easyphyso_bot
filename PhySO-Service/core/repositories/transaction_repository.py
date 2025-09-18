# core/repositories/transaction_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.transaction import Transaction

class TransactionRepository(ABC):
    """Abstract base class defining the interface for transaction data persistence."""

    @abstractmethod
    def add(self, transaction: Transaction) -> Transaction:
        """Adds a new transaction record."""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieves a transaction by its database ID."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[Transaction]:
        """Retrieves all transactions for a specific user."""
        pass
