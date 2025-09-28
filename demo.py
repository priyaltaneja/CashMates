#!/usr/bin/env python3
"""
demo script for cashmates application.
this script demonstrates the core functionality without requiring cli arguments.
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from roomiesplit.models import User, Group, Expense, Split, SplitType
from roomiesplit.persistence import CSVStorage
from roomiesplit.services import LedgerService, SettlementService, ConsoleNotificationService
from roomiesplit.utils.money import to_decimal


def main():
    """demonstrate cashmates functionality."""
    print("=== CashMates Demo ===\n")
    
    # Initialize services
    storage = CSVStorage("demo_data")
    ledger_service = LedgerService(storage)
    settlement_service = SettlementService()
    notification_service = ConsoleNotificationService()
    
    print("1. Creating users...")
    users = [
        User(id="alice", name="Alice"),
        User(id="bob", name="Bob"),
        User(id="charlie", name="Charlie")
    ]
    
    for user in users:
        storage.save_user(user)
        print(f"   Created: {user}")
    
    print("\n2. Creating group...")
    group = Group(
        id="apartment",
        name="Apartment 4B",
        member_ids={"alice", "bob", "charlie"}
    )
    storage.save_group(group)
    print(f"   Created: {group}")
    
    print("\n3. Adding expenses...")
    
    # Dinner expense - equal split
    dinner_expense = Expense(
        id="dinner",
        group_id="apartment",
        payer_id="alice",
        amount=to_decimal("60.00"),
        description="Dinner at restaurant",
        timestamp=datetime.now(),
        splits=[
            Split("dinner", "alice", SplitType.EQUAL, to_decimal("20.00")),
            Split("dinner", "bob", SplitType.EQUAL, to_decimal("20.00")),
            Split("dinner", "charlie", SplitType.EQUAL, to_decimal("20.00"))
        ]
    )
    storage.save_expense(dinner_expense)
    print(f"   Added: {dinner_expense}")
    
    # Groceries expense - percentage split
    groceries_expense = Expense(
        id="groceries",
        group_id="apartment",
        payer_id="bob",
        amount=to_decimal("100.00"),
        description="Weekly groceries",
        timestamp=datetime.now(),
        splits=[
            Split("groceries", "alice", SplitType.PERCENT, to_decimal("50.00")),  # 50%
            Split("groceries", "bob", SplitType.PERCENT, to_decimal("30.00")),    # 30%
            Split("groceries", "charlie", SplitType.PERCENT, to_decimal("20.00")) # 20%
        ]
    )
    storage.save_expense(groceries_expense)
    print(f"   Added: {groceries_expense}")
    
    print("\n4. Calculating balances...")
    balances = ledger_service.calculate_balances("apartment")
    summary = ledger_service.get_group_summary("apartment")
    
    print("   Current balances:")
    for user_id, balance in balances.items():
        user_name = next(u.name for u in users if u.id == user_id)
        if balance > 0:
            print(f"     {user_name}: +${balance} (owed to them)")
        elif balance < 0:
            print(f"     {user_name}: -${abs(balance)} (owes)")
        else:
            print(f"     {user_name}: $0 (even)")
    
    print("\n5. Suggesting settlements...")
    settlements = settlement_service.suggest_settlements(balances)
    
    if settlements:
        print("   Optimal settlement transactions:")
        for settlement in settlements:
            from_name = next(u.name for u in users if u.id == settlement['from_user'])
            to_name = next(u.name for u in users if u.id == settlement['to_user'])
            print(f"     {from_name} -> {to_name}: ${settlement['amount']}")
    else:
        print("   No settlements needed - everyone is even!")
    
    print("\n6. Recording a payment...")
    storage.save_payment("payment1", "apartment", "charlie", "alice", to_decimal("10.00"))
    print("   Charlie paid Alice $10.00")
    
    print("\n7. Updated balances after payment...")
    new_balances = ledger_service.calculate_balances("apartment")
    for user_id, balance in new_balances.items():
        user_name = next(u.name for u in users if u.id == user_id)
        if balance > 0:
            print(f"     {user_name}: +${balance} (owed to them)")
        elif balance < 0:
            print(f"     {user_name}: -${abs(balance)} (owes)")
        else:
            print(f"     {user_name}: $0 (even)")
    
    print("\n8. Sending notifications...")
    notification_service.send_balance_update("Alice", {
        "Bob": "-$20.00",
        "Charlie": "+$10.00"
    })
    
    print("\n9. Settlement suggestions after payment...")
    final_settlements = settlement_service.suggest_settlements(new_balances)
    if final_settlements:
        print("   Final settlement transactions:")
        for settlement in final_settlements:
            from_name = next(u.name for u in users if u.id == settlement['from_user'])
            to_name = next(u.name for u in users if u.id == settlement['to_user'])
            print(f"     {from_name} -> {to_name}: ${settlement['amount']}")
    
    print("\n=== Demo Complete ===")
    print("Data saved to 'demo_data/' directory")
    print("Run 'python src/roomiesplit/main.py --help' to see CLI usage")


if __name__ == "__main__":
    main()
