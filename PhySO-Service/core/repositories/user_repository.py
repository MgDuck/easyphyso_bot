# core/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.user import User

class UserRepository(ABC):
    """Abstract base class defining the interface for user data persistence."""

    @abstractmethod
    def add(self, user: User) -> User:
        """Adds a new user to the repository.

        Args:
            user (User): The user entity to add (without an ID initially).

        Returns:
            User: The added user entity, potentially updated with a database ID.
        """
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their database ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Optional[User]: The user entity if found, otherwise None.
        """
        pass

    @abstractmethod
    def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Retrieves a user by their Telegram ID.

        Args:
            telegram_id (str): The Telegram ID of the user to retrieve.

        Returns:
            Optional[User]: The user entity if found, otherwise None.
        """
        pass

    @abstractmethod
    def update_balance(self, user_id: int, new_balance: float) -> bool:
        """Updates the balance for a specific user.

        Args:
            user_id (int): The ID of the user whose balance needs updating.
            new_balance (float): The new balance amount.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        pass

    @abstractmethod
    def list_all(self) -> List[User]:
        """Retrieves a list of all users.

        Returns:
            List[User]: A list of all user entities.
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[User]:
        """Retrieves a user by their name.

        Args:
            name (str): The name of the user to retrieve.

        Returns:
            Optional[User]: The user entity if found, otherwise None.
        """
        pass

    @abstractmethod
    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        """Updates the password_hash for a specific user.

        Args:
            user_id (int): The ID of the user.
            password_hash (str): The new password hash.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        pass

    @abstractmethod
    def update_api_key(self, user_id: int, api_key: str) -> bool:
        """Updates the api_key for a specific user.

        Args:
            user_id (int): The ID of the user.
            api_key (str): The new API key.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Retrieves a user by their API key.

        Args:
            api_key (str): The API key of the user to retrieve.

        Returns:
            Optional[User]: The user entity if found, otherwise None.
        """
        pass
