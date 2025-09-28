#!/usr/bin/env python3
"""quick test to verify core functionality."""

import sys
import os
from decimal import Decimal

# add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from roomiesplit.utils.money import to_decimal, round_money
from roomiesplit.services import SettlementService
from roomiesplit.models import SplitType

def test_money_utils():
    """test money utility functions."""
    print("Testing money utilities...")
    
    # Test decimal conversion
    amount = to_decimal("10.50")
    assert amount == Decimal("10.50")
    print("+ Decimal conversion works")
    
    # Test rounding
    rounded = round_money("10.555")
    assert rounded == Decimal("10.56")
    print("+ Money rounding works")

def test_settlement_service():
    """test settlement service."""
    print("\nTesting settlement service...")
    
    service = SettlementService()
    
    # Simple settlement test
    balances = {
        "alice": Decimal("20.00"),
        "bob": Decimal("-20.00")
    }
    
    settlements = service.suggest_settlements(balances)
    assert len(settlements) == 1
    assert settlements[0]['amount'] == Decimal("20.00")
    print("+ Settlement calculation works")

def test_split_types():
    """test split type constants."""
    print("\nTesting split types...")
    
    assert SplitType.EQUAL == "equal"
    assert SplitType.EXACT == "exact"
    assert SplitType.PERCENT == "percent"
    print("+ Split types defined correctly")

if __name__ == "__main__":
    print("=== Quick Functionality Test ===\n")
    
    try:
        test_money_utils()
        test_settlement_service()
        test_split_types()
        
        print("\n[SUCCESS] All core functionality tests passed!")
        print("The CashMates application is working correctly.")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        sys.exit(1)
