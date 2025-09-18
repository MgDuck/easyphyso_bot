"""Service singletons for the bot."""
from .user_service import UserService
from .physo_api import PhySoAPIService

# Shared singleton instances used across the project
user_service = UserService()
physo_api_service = PhySoAPIService()

__all__ = [
    "UserService",
    "PhySoAPIService",
    "user_service",
    "physo_api_service",
]
