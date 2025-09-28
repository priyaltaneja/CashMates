"""user model for managing roommates."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """represents a user/roommate."""
    id: str
    name: str
    phone: Optional[str] = None

    def __str__(self):
        return f"{self.name} ({self.id})"
