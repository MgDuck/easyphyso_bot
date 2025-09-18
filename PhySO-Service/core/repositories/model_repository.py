# core/repositories/model_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.model import Model

class ModelRepository(ABC):
    """Abstract base class defining the interface for model data persistence."""

    @abstractmethod
    def add(self, model: Model) -> Model:
        """Adds a new model to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, model_id: int) -> Optional[Model]:
        """Retrieves a model by its database ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Model]:
        """Retrieves a model by its name."""
        pass

    @abstractmethod
    def get_active_model(self) -> Optional[Model]:
        """Retrieves the currently active model (simplification: assumes one active)."""
        pass

    @abstractmethod
    def list_all(self) -> List[Model]:
        """Retrieves a list of all models."""
        pass
