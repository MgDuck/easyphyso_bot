# core/entities/prediction.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

class Prediction(BaseModel):
    """Represents a PhySO symbolic regression request and its result."""
    id: Optional[int] = None  # Database ID
    # Unique identifier for API access
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None  # Foreign key to User
    model_id: Optional[int] = None  # Foreign key to Model (PhySO config)
    # Input data and parameters
    input_data: Optional[str] = None  # CSV data as string
    y_name: str = "y"  # Target variable name
    x_names: Optional[List[str]] = None  # Input variable names
    epochs: int = 50  # Number of epochs
    op_names: Optional[List[str]] = None  # Operations to use
    free_consts_names: Optional[List[str]] = None  # Free constants
    run_config: str = "config0"  # PhySO configuration
    stop_reward: float = 0.999  # Stopping criterion
    parallel_mode: bool = False  # Parallel execution
    # Results
    best_formula: Optional[str] = None  # Best discovered formula
    best_r2: Optional[float] = None  # Best R² score
    pareto_count: int = 0  # Number of Pareto-optimal solutions
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata
    total_cost: Optional[float] = None
    status: str = 'pending'  # e.g., pending, processing, completed, failed
    # Automatically set on creation
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    queue_time: Optional[int] = None  # Time spent in queue (ms)
    process_time: Optional[int] = None  # Time spent processing (ms)

