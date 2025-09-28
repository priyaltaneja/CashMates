"""settlement service for optimizing debt resolution."""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Tuple

from ..utils.money import round_money


class SettlementService:
    """service for suggesting optimal settlement transactions."""
    
    def suggest_settlements(self, balances: Dict[str, Decimal]) -> List[Dict[str, any]]:
        """suggest minimal transactions to settle all debts."""
        # separate creditors and debtors
        creditors = {user: balance for user, balance in balances.items() if balance > 0}
        debtors = {user: abs(balance) for user, balance in balances.items() if balance < 0}
        
        settlements = []
        
        # convert to sorted lists for processing
        creditor_list = sorted(creditors.items(), key=lambda x: x[1], reverse=True)
        debtor_list = sorted(debtors.items(), key=lambda x: x[1], reverse=True)
        
        creditor_idx = 0
        debtor_idx = 0
        
        while creditor_idx < len(creditor_list) and debtor_idx < len(debtor_list):
            creditor_user, creditor_amount = creditor_list[creditor_idx]
            debtor_user, debtor_amount = debtor_list[debtor_idx]
            
            # calculate settlement amount
            settlement_amount = min(creditor_amount, debtor_amount)
            settlement_amount = round_money(settlement_amount)
            
            if settlement_amount > 0:
                settlements.append({
                    'from_user': debtor_user,
                    'to_user': creditor_user,
                    'amount': settlement_amount,
                    'description': f"{debtor_user} pays {creditor_user} ${settlement_amount}"
                })
            
            # update amounts
            creditor_amount -= settlement_amount
            debtor_amount -= settlement_amount
            
            # update lists
            if creditor_amount <= 0:
                creditor_idx += 1
            else:
                creditor_list[creditor_idx] = (creditor_user, creditor_amount)
            
            if debtor_amount <= 0:
                debtor_idx += 1
            else:
                debtor_list[debtor_idx] = (debtor_user, debtor_amount)
        
        return settlements
    
    def calculate_settlement_stats(self, balances: Dict[str, Decimal], 
                                 settlements: List[Dict]) -> Dict[str, any]:
        """Calculate statistics about the settlement."""
        total_debt = sum(abs(balance) for balance in balances.values() if balance < 0)
        total_settlements = sum(settlement['amount'] for settlement in settlements)
        
        return {
            'total_debt': total_debt,
            'settlement_count': len(settlements),
            'total_settlements': total_settlements,
            'efficiency': len(settlements) / len([b for b in balances.values() if b != 0]) if balances else 0
        }
