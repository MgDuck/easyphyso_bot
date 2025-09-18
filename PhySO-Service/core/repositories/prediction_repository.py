# core/repositories/prediction_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.prediction import Prediction

class PredictionRepository(ABC):
    """Abstract base class defining the interface for prediction data persistence."""

    @abstractmethod
    def add(self, prediction: Prediction) -> Prediction:
        """Adds a new prediction record."""
        pass

    @abstractmethod
    def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        """Retrieves a prediction by its database ID."""
        pass

    @abstractmethod
    def get_by_uuid(self, uuid: str) -> Optional[Prediction]:
        """Retrieves a prediction by its unique UUID."""
        pass

    @abstractmethod
    def update(self, prediction: Prediction) -> bool:
        """Updates an existing prediction record."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[Prediction]:
        """Retrieves all predictions for a specific user."""
        pass
