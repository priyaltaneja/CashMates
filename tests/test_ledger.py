"""Tests for ledger service."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.roomiesplit.models import User, Group, Expense, Split, SplitType
from src.roomiesplit.persistence import CSVStorage
from src.roomiesplit.services import LedgerService
from src.roomiesplit.utils.money import to_decimal


class TestLedgerService:
    """Test cases for LedgerService."""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Create temporary storage for testing."""
        return CSVStorage(str(tmp_path))
    
    @pytest.fixture
    def ledger_service(self, storage):
        """Create ledger service with temporary storage."""
        return LedgerService(storage)
    
    @pytest.fixture
    def sample_users(self, storage):
        """Create sample users for testing."""
        users = [
            User(id="user1", name="Alice"),
            User(id="user2", name="Bob"),
            User(id="user3", name="Charlie")
        ]
        for user in users:
            storage.save_user(user)
        return users
    
    @pytest.fixture
    def sample_group(self, storage, sample_users):
        """Create sample group for testing."""
        group = Group(
            id="group1",
            name="Test Group",
            member_ids={"user1", "user2", "user3"}
        )
        storage.save_group(group)
        return group
    
    def test_equal_split_expense(self, ledger_service, storage, sample_group):
        """Test equal split expense calculation."""
        expense = Expense(
            id="expense1",
            group_id="group1",
            payer_id="user1",
            amount=to_decimal("60.00"),
            description="Dinner",
            timestamp=datetime.now(),
            splits=[
                Split("expense1", "user1", SplitType.EQUAL, to_decimal("20.00")),
                Split("expense1", "user2", SplitType.EQUAL, to_decimal("20.00")),
                Split("expense1", "user3", SplitType.EQUAL, to_decimal("20.00"))
            ]
        )
        storage.save_expense(expense)
        
        balances = ledger_service.calculate_balances("group1")
        
        assert balances["user1"] == to_decimal("40.00")  # Paid 60, owes 20
        assert balances["user2"] == to_decimal("-20.00")  # Owes 20
        assert balances["user3"] == to_decimal("-20.00")  # Owes 20
    
    def test_percent_split_expense(self, ledger_service, storage, sample_group):
        """Test percentage split expense calculation."""
        expense = Expense(
            id="expense2",
            group_id="group1",
            payer_id="user1",
            amount=to_decimal("100.00"),
            description="Groceries",
            timestamp=datetime.now(),
            splits=[
                Split("expense2", "user1", SplitType.PERCENT, to_decimal("50.00")),  # 50%
                Split("expense2", "user2", SplitType.PERCENT, to_decimal("30.00")),  # 30%
                Split("expense2", "user3", SplitType.PERCENT, to_decimal("20.00"))   # 20%
            ]
        )
        storage.save_expense(expense)
        
        balances = ledger_service.calculate_balances("group1")
        
        assert balances["user1"] == to_decimal("50.00")   # Paid 100, owes 50
        assert balances["user2"] == to_decimal("-30.00")  # Owes 30
        assert balances["user3"] == to_decimal("-20.00")  # Owes 20
    
    def test_payment_recording(self, ledger_service, storage, sample_group):
        """Test payment recording affects balances."""
        # Create expense first
        expense = Expense(
            id="expense3",
            group_id="group1",
            payer_id="user1",
            amount=to_decimal("30.00"),
            description="Uber",
            timestamp=datetime.now(),
            splits=[
                Split("expense3", "user1", SplitType.EQUAL, to_decimal("10.00")),
                Split("expense3", "user2", SplitType.EQUAL, to_decimal("10.00")),
                Split("expense3", "user3", SplitType.EQUAL, to_decimal("10.00"))
            ]
        )
        storage.save_expense(expense)
        
        # Record payment
        storage.save_payment("payment1", "group1", "user2", "user1", to_decimal("10.00"))
        
        balances = ledger_service.calculate_balances("group1")
        
        assert balances["user1"] == to_decimal("10.00")  # Paid 30, owes 10, received 10
        assert balances["user2"] == to_decimal("0.00")   # Owed 10, paid 10
        assert balances["user3"] == to_decimal("-10.00") # Still owes 10
    
    def test_group_summary(self, ledger_service, storage, sample_group):
        """Test group summary calculation."""
        # Create expenses
        expense1 = Expense(
            id="expense4",
            group_id="group1",
            payer_id="user1",
            amount=to_decimal("60.00"),
            description="Expense 1",
            timestamp=datetime.now(),
            splits=[
                Split("expense4", "user1", SplitType.EQUAL, to_decimal("20.00")),
                Split("expense4", "user2", SplitType.EQUAL, to_decimal("20.00")),
                Split("expense4", "user3", SplitType.EQUAL, to_decimal("20.00"))
            ]
        )
        storage.save_expense(expense1)
        
        summary = ledger_service.get_group_summary("group1")
        
        assert len(summary['balances']) == 3
        assert summary['total_owed'] == to_decimal("40.00")
        assert summary['total_due'] == to_decimal("40.00")
        assert summary['is_balanced'] is True
        assert len(summary['creditors']) == 1
        assert len(summary['debtors']) == 2
        assert len(summary['even']) == 0
