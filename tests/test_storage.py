"""Tests for CSV storage."""

import pytest
import tempfile
import shutil
from datetime import datetime
from decimal import Decimal

from src.roomiesplit.models import User, Group, Expense, Split, SplitType
from src.roomiesplit.persistence import CSVStorage
from src.roomiesplit.utils.money import to_decimal


class TestCSVStorage:
    """Test cases for CSVStorage."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance with temporary directory."""
        return CSVStorage(temp_dir)
    
    def test_user_operations(self, storage):
        """Test user save and load operations."""
        user = User(id="user1", name="Alice", phone="+1234567890")
        storage.save_user(user)
        
        users = storage.load_users()
        assert len(users) == 1
        assert users[0].id == "user1"
        assert users[0].name == "Alice"
        assert users[0].phone == "+1234567890"
    
    def test_group_operations(self, storage):
        """Test group save and load operations."""
        group = Group(
            id="group1",
            name="Test Group",
            member_ids={"user1", "user2", "user3"}
        )
        storage.save_group(group)
        
        groups = storage.load_groups()
        assert len(groups) == 1
        assert groups[0].id == "group1"
        assert groups[0].name == "Test Group"
        assert groups[0].member_ids == {"user1", "user2", "user3"}
    
    def test_expense_operations(self, storage):
        """Test expense save and load operations."""
        timestamp = datetime.now()
        expense = Expense(
            id="expense1",
            group_id="group1",
            payer_id="user1",
            amount=to_decimal("60.00"),
            description="Dinner",
            timestamp=timestamp,
            splits=[
                Split("expense1", "user1", SplitType.EQUAL, to_decimal("20.00")),
                Split("expense1", "user2", SplitType.EQUAL, to_decimal("20.00")),
                Split("expense1", "user3", SplitType.EQUAL, to_decimal("20.00"))
            ]
        )
        storage.save_expense(expense)
        
        expenses = storage.load_expenses()
        assert len(expenses) == 1
        assert expenses[0].id == "expense1"
        assert expenses[0].group_id == "group1"
        assert expenses[0].payer_id == "user1"
        assert expenses[0].amount == to_decimal("60.00")
        assert expenses[0].description == "Dinner"
        assert len(expenses[0].splits) == 3
    
    def test_payment_operations(self, storage):
        """Test payment save and load operations."""
        storage.save_payment(
            payment_id="payment1",
            group_id="group1",
            from_user="user1",
            to_user="user2",
            amount=to_decimal("25.50")
        )
        
        payments = storage.load_payments()
        assert len(payments) == 1
        assert payments[0]['id'] == "payment1"
        assert payments[0]['group_id'] == "group1"
        assert payments[0]['from_user'] == "user1"
        assert payments[0]['to_user'] == "user2"
        assert payments[0]['amount'] == to_decimal("25.50")
    
    def test_file_initialization(self, temp_dir):
        """Test that CSV files are initialized with headers."""
        storage = CSVStorage(temp_dir)
        
        # Check that all required files exist
        import os
        expected_files = [
            'users.csv', 'groups.csv', 'group_members.csv',
            'expenses.csv', 'splits.csv', 'payments.csv'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(temp_dir, filename)
            assert os.path.exists(filepath)
            
            # Check that file has headers
            with open(filepath, 'r') as f:
                first_line = f.readline().strip()
                assert first_line  # Should not be empty
    
    def test_empty_data_handling(self, storage):
        """Test handling of empty data scenarios."""
        # Test loading from empty files
        users = storage.load_users()
        groups = storage.load_groups()
        expenses = storage.load_expenses()
        payments = storage.load_payments()
        
        assert users == []
        assert groups == []
        assert expenses == []
        assert payments == []
    
    def test_multiple_operations(self, storage):
        """Test multiple save/load operations."""
        # Save multiple users
        users = [
            User(id="user1", name="Alice"),
            User(id="user2", name="Bob"),
            User(id="user3", name="Charlie")
        ]
        
        for user in users:
            storage.save_user(user)
        
        loaded_users = storage.load_users()
        assert len(loaded_users) == 3
        
        # Save multiple expenses
        expenses = [
            Expense(
                id="expense1",
                group_id="group1",
                payer_id="user1",
                amount=to_decimal("30.00"),
                description="Expense 1",
                timestamp=datetime.now(),
                splits=[Split("expense1", "user1", SplitType.EQUAL, to_decimal("15.00"))]
            ),
            Expense(
                id="expense2",
                group_id="group1",
                payer_id="user2",
                amount=to_decimal("60.00"),
                description="Expense 2",
                timestamp=datetime.now(),
                splits=[Split("expense2", "user2", SplitType.EQUAL, to_decimal("30.00"))]
            )
        ]
        
        for expense in expenses:
            storage.save_expense(expense)
        
        loaded_expenses = storage.load_expenses()
        assert len(loaded_expenses) == 2
