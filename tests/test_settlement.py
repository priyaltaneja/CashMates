"""Tests for settlement service."""

import pytest
from decimal import Decimal

from src.roomiesplit.services import SettlementService
from src.roomiesplit.utils.money import to_decimal


class TestSettlementService:
    """Test cases for SettlementService."""
    
    @pytest.fixture
    def settlement_service(self):
        """Create settlement service for testing."""
        return SettlementService()
    
    def test_simple_settlement(self, settlement_service):
        """Test simple two-person settlement."""
        balances = {
            "user1": to_decimal("20.00"),  # User1 is owed 20
            "user2": to_decimal("-20.00")  # User2 owes 20
        }
        
        settlements = settlement_service.suggest_settlements(balances)
        
        assert len(settlements) == 1
        assert settlements[0]['from_user'] == "user2"
        assert settlements[0]['to_user'] == "user1"
        assert settlements[0]['amount'] == to_decimal("20.00")
    
    def test_three_way_settlement(self, settlement_service):
        """Test three-way settlement scenario."""
        balances = {
            "user1": to_decimal("30.00"),  # User1 is owed 30
            "user2": to_decimal("-20.00"), # User2 owes 20
            "user3": to_decimal("-10.00")  # User3 owes 10
        }
        
        settlements = settlement_service.suggest_settlements(balances)
        
        assert len(settlements) == 2
        
        # Check that all debts are settled
        total_settled = sum(s['amount'] for s in settlements)
        assert total_settled == to_decimal("30.00")
        
        # Verify individual settlements
        settlement_amounts = [s['amount'] for s in settlements]
        assert to_decimal("20.00") in settlement_amounts
        assert to_decimal("10.00") in settlement_amounts
    
    def test_complex_settlement(self, settlement_service):
        """Test complex multi-person settlement."""
        balances = {
            "user1": to_decimal("50.00"),  # User1 is owed 50
            "user2": to_decimal("30.00"),  # User2 is owed 30
            "user3": to_decimal("-40.00"), # User3 owes 40
            "user4": to_decimal("-40.00")  # User4 owes 40
        }
        
        settlements = settlement_service.suggest_settlements(balances)
        
        # Should have minimal transactions
        assert len(settlements) <= 3
        
        # Verify all debts are settled
        total_settled = sum(s['amount'] for s in settlements)
        assert total_settled == to_decimal("80.00")
        
        # Check that no user is both giving and receiving
        giving_users = {s['from_user'] for s in settlements}
        receiving_users = {s['to_user'] for s in settlements}
        assert not giving_users.intersection(receiving_users)
    
    def test_even_balances(self, settlement_service):
        """Test scenario where everyone is even."""
        balances = {
            "user1": to_decimal("0.00"),
            "user2": to_decimal("0.00"),
            "user3": to_decimal("0.00")
        }
        
        settlements = settlement_service.suggest_settlements(balances)
        
        assert len(settlements) == 0
    
    def test_settlement_stats(self, settlement_service):
        """Test settlement statistics calculation."""
        balances = {
            "user1": to_decimal("30.00"),
            "user2": to_decimal("-20.00"),
            "user3": to_decimal("-10.00")
        }
        
        settlements = settlement_service.suggest_settlements(balances)
        stats = settlement_service.calculate_settlement_stats(balances, settlements)
        
        assert stats['total_debt'] == to_decimal("30.00")
        assert stats['settlement_count'] == 2
        assert stats['total_settlements'] == to_decimal("30.00")
        assert stats['efficiency'] == 2 / 3  # 2 transactions for 3 non-zero balances
