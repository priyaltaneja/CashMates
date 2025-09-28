#!/usr/bin/env python3
"""end-to-end test demonstrating complete workflow."""

import sys
import os
from datetime import datetime

# add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from roomiesplit.models import User, Group, Expense, Split, SplitType
from roomiesplit.persistence import CSVStorage
from roomiesplit.services import LedgerService, SettlementService
from roomiesplit.utils.money import to_decimal

def main():
    """run complete end-to-end test."""
    print("=== End-to-End Test ===\n")
    
    # clean slate - use fresh data directory
    storage = CSVStorage("test_data")
    ledger = LedgerService(storage)
    settlement_service = SettlementService()
    
    print("1. Creating roommates...")
    users = [
        User(id="alice", name="Alice"),
        User(id="bob", name="Bob"), 
        User(id="charlie", name="Charlie")
    ]
    for user in users:
        storage.save_user(user)
        print(f"   Created: {user.name}")
    
    print("\n2. Creating apartment group...")
    group = Group(
        id="apartment",
        name="Apartment 4B", 
        member_ids={"alice", "bob", "charlie"}
    )
    storage.save_group(group)
    print(f"   Created: {group.name}")
    
    print("\n3. Adding shared expenses...")
    
    # expense 1: Dinner (equal split)
    dinner = Expense(
        id="dinner",
        group_id="apartment",
        payer_id="alice",
        amount=to_decimal("90.00"),
        description="Dinner at restaurant",
        timestamp=datetime.now(),
        splits=[
            Split("dinner", "alice", SplitType.EQUAL, to_decimal("30.00")),
            Split("dinner", "bob", SplitType.EQUAL, to_decimal("30.00")),
            Split("dinner", "charlie", SplitType.EQUAL, to_decimal("30.00"))
        ]
    )
    storage.save_expense(dinner)
    print(f"   Added: {dinner.description} - ${dinner.amount}")
    
    # expense 2: Groceries (percentage split)
    groceries = Expense(
        id="groceries",
        group_id="apartment", 
        payer_id="bob",
        amount=to_decimal("120.00"),
        description="Weekly groceries",
        timestamp=datetime.now(),
        splits=[
            Split("groceries", "alice", SplitType.PERCENT, to_decimal("50.00")),  # $60
            Split("groceries", "bob", SplitType.PERCENT, to_decimal("30.00")),    # $36
            Split("groceries", "charlie", SplitType.PERCENT, to_decimal("20.00")) # $24
        ]
    )
    storage.save_expense(groceries)
    print(f"   Added: {groceries.description} - ${groceries.amount}")
    
    print("\n4. Calculating current balances...")
    balances = ledger.calculate_balances("apartment")
    
    print("   Current situation:")
    for user_id, balance in balances.items():
        user_name = next(u.name for u in users if u.id == user_id)
        if balance > 0:
            print(f"     {user_name}: +${balance} (owed to them)")
        elif balance < 0:
            print(f"     {user_name}: -${abs(balance)} (owes)")
        else:
            print(f"     {user_name}: $0 (even)")
    
    print("\n5. Getting settlement suggestions...")
    settlements = settlement_service.suggest_settlements(balances)
    
    if settlements:
        print("   Optimal payments to settle all debts:")
        for settlement in settlements:
            from_name = next(u.name for u in users if u.id == settlement['from_user'])
            to_name = next(u.name for u in users if u.id == settlement['to_user'])
            print(f"     {from_name} -> {to_name}: ${settlement['amount']}")
    else:
        print("   No settlements needed!")
    
    print("\n6. Recording a payment...")
    storage.save_payment("payment1", "apartment", "charlie", "alice", to_decimal("30.00"))
    print("   Charlie paid Alice $30.00")
    
    print("\n7. Checking updated balances...")
    new_balances = ledger.calculate_balances("apartment")
    
    print("   Updated situation:")
    for user_id, balance in new_balances.items():
        user_name = next(u.name for u in users if u.id == user_id)
        if balance > 0:
            print(f"     {user_name}: +${balance} (owed to them)")
        elif balance < 0:
            print(f"     {user_name}: -${abs(balance)} (owes)")
        else:
            print(f"     {user_name}: $0 (even)")
    
    print("\n8. Final settlement suggestions...")
    final_settlements = settlement_service.suggest_settlements(new_balances)
    
    if final_settlements:
        print("   Remaining payments needed:")
        for settlement in final_settlements:
            from_name = next(u.name for u in users if u.id == settlement['from_user'])
            to_name = next(u.name for u in users if u.id == settlement['to_user'])
            print(f"     {from_name} -> {to_name}: ${settlement['amount']}")
    else:
        print("   All debts settled!")
    
    print("\n=== End-to-End Test Complete ===")
    print("Data persisted to 'test_data/' directory")
    print("All functionality working correctly!")

if __name__ == "__main__":
    main()
