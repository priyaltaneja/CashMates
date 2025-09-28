"""expense model for managing shared expenses."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

from ..utils.money import to_decimal


class SplitType:
    """split calculation types."""
    EQUAL = "equal"
    EXACT = "exact"
    PERCENT = "percent"


@dataclass
class Split:
    """represents how an expense is split among users."""
    expense_id: str
    user_id: str
    share_type: str
    value: Decimal

    def __post_init__(self):
        self.value = to_decimal(self.value)


@dataclass
class Expense:
    """represents a shared expense."""
    id: str
    group_id: str
    payer_id: str
    amount: Decimal
    description: str
    timestamp: datetime
    splits: List[Split]

    def __post_init__(self):
        self.amount = to_decimal(self.amount)

    @property
    def split_total(self) -> Decimal:
        """calculate total of all splits."""
        return sum(split.value for split in self.splits)

    def validate_splits(self) -> bool:
        """validate that splits are correct for the split type."""
        if not self.splits:
            return False

        split_type = self.splits[0].share_type
        
        if split_type == SplitType.EQUAL:
            expected_share = self.amount / len(self.splits)
            return all(split.value == expected_share for split in self.splits)
        
        elif split_type == SplitType.EXACT:
            return self.split_total == self.amount
        
        elif split_type == SplitType.PERCENT:
            return self.split_total == Decimal('100')
        
        return False

    def __str__(self):
        return f"{self.description}: ${self.amount} by {self.payer_id}"
