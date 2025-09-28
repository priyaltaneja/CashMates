"""ledger service for calculating balances and managing expenses."""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Tuple

from ..models.user import User
from ..models.group import Group
from ..models.expense import Expense
from ..utils.money import to_decimal, round_money


class LedgerService:
    """service for managing financial ledger calculations."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def calculate_balances(self, group_id: str) -> Dict[str, Decimal]:
        """calculate net balances for all users in a group."""
        expenses = self.storage.load_expenses()
        payments = self.storage.load_payments()
        
        # filter for group
        group_expenses = [e for e in expenses if e.group_id == group_id]
        group_payments = [p for p in payments if p['group_id'] == group_id]
        
        balances = defaultdict(Decimal)
        
        # process expenses
        for expense in group_expenses:
            # payer gets credited (positive balance)
            balances[expense.payer_id] += expense.amount
            
            # splitters get debited (negative balance)
            for split in expense.splits:
                if split.share_type == 'percent':
                    # convert percentage to dollar amount
                    share_amount = (expense.amount * split.value) / Decimal('100')
                else:
                    share_amount = split.value
                
                balances[split.user_id] -= round_money(share_amount)
        
        # process payments
        for payment in group_payments:
            # payment from user a to user b
            balances[payment['from_user']] += payment['amount']  # a gets credit
            balances[payment['to_user']] -= payment['amount']    # b gets debit
        
        # round all balances
        return {user_id: round_money(balance) for user_id, balance in balances.items()}
    
    def get_group_summary(self, group_id: str) -> Dict[str, any]:
        """get comprehensive summary for a group."""
        balances = self.calculate_balances(group_id)
        
        # calculate totals
        total_owed = sum(balance for balance in balances.values() if balance < 0)
        total_due = sum(balance for balance in balances.values() if balance > 0)
        
        # categorize users
        creditors = {user_id: balance for user_id, balance in balances.items() if balance > 0}
        debtors = {user_id: balance for user_id, balance in balances.items() if balance < 0}
        even = {user_id: balance for user_id, balance in balances.items() if balance == 0}
        
        return {
            'balances': balances,
            'creditors': creditors,
            'debtors': debtors,
            'even': even,
            'total_owed': abs(total_owed),
            'total_due': total_due,
            'is_balanced': abs(total_owed) == total_due
        }
    
    def validate_expense_split(self, amount: Decimal, splits: List[Dict]) -> Tuple[bool, str]:
        """validate that expense splits are correct."""
        if not splits:
            return False, "No splits provided"
        
        split_type = splits[0].get('share_type')
        
        if split_type == 'equal':
            expected_share = amount / len(splits)
            for split in splits:
                if split['value'] != expected_share:
                    return False, f"Equal split should be ${expected_share} each"
        
        elif split_type == 'exact':
            total = sum(to_decimal(split['value']) for split in splits)
            if total != amount:
                return False, f"Exact splits sum to ${total}, but expense is ${amount}"
        
        elif split_type == 'percent':
            total_percent = sum(to_decimal(split['value']) for split in splits)
            if total_percent != Decimal('100'):
                return False, f"Percent splits sum to {total_percent}%, should be 100%"
        
        else:
            return False, f"Unknown split type: {split_type}"
        
        return True, "Valid split"
