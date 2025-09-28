"""group model for managing roommate groups."""

from dataclasses import dataclass
from typing import List, Set


@dataclass
class Group:
    """represents a group of roommates."""
    id: str
    name: str
    member_ids: Set[str]

    @property
    def member_count(self) -> int:
        """return number of members in group."""
        return len(self.member_ids)

    def add_member(self, user_id: str) -> None:
        """add a user to the group."""
        self.member_ids.add(user_id)

    def remove_member(self, user_id: str) -> None:
        """remove a user from the group."""
        self.member_ids.discard(user_id)

    def has_member(self, user_id: str) -> bool:
        """check if user is a member of the group."""
        return user_id in self.member_ids

    def __str__(self):
        return f"{self.name} ({self.member_count} members)"
