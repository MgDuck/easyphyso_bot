# core/entities/model.py
from dataclasses import dataclass

@dataclass
class Model:
    """Represents a PhySO configuration available in the system."""
    id: int | None = None # Database ID
    name: str | None = None # Model name (e.g., 'config0', 'config1', 'config2')
    description: str | None = None # Optional description
    base_price: float = 0.0 # Base price for using this configuration
    epoch_price: float = 0.0 # Price per epoch
    is_active: bool = True # Whether the configuration is currently available for use
