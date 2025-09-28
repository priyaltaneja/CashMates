"""command-line interface for roomiesplit."""

import argparse
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List

from .models import User, Group, Expense, Split, SplitType
from .persistence import CSVStorage
from .services import LedgerService, SettlementService, TwilioNotificationService
from .utils.money import to_decimal


class CashMatesCLI:
    """command-line interface for cashmates."""
    
    def __init__(self):
        self.storage = CSVStorage()
        self.ledger_service = LedgerService(self.storage)
        self.settlement_service = SettlementService()
        self.notification_service = TwilioNotificationService()
    
    def create_user(self, name: str, phone: str = None) -> str:
        """create a new user."""
        user_id = str(uuid.uuid4())[:8]
        user = User(id=user_id, name=name, phone=phone)
        self.storage.save_user(user)
        print(f"Created user: {user}")
        return user_id
    
    def create_group(self, group_name: str, member_names: List[str]) -> str:
        """create a new group with members."""
        group_id = str(uuid.uuid4())[:8]
        
        # find or create users
        existing_users = {user.name: user.id for user in self.storage.load_users()}
        member_ids = set()
        
        for name in member_names:
            if name in existing_users:
                member_ids.add(existing_users[name])
            else:
                # create new user
                user_id = self.create_user(name)
                member_ids.add(user_id)
        
        group = Group(id=group_id, name=group_name, member_ids=member_ids)
        self.storage.save_group(group)
        print(f"Created group: {group}")
        return group_id
    
    def add_expense(self, group_name: str, paid_by: str, amount: float, 
                   description: str, split_type: str, shares: List[str]) -> str:
        """Add a new expense to a group."""
        # Find group
        groups = self.storage.load_groups()
        group = next((g for g in groups if g.name == group_name), None)
        if not group:
            raise ValueError(f"Group '{group_name}' not found")
        
        # Find payer
        users = {user.name: user.id for user in self.storage.load_users()}
        if paid_by not in users:
            raise ValueError(f"User '{paid_by}' not found")
        
        # Parse shares
        expense_splits = []
        if split_type == SplitType.EQUAL:
            share_amount = to_decimal(amount) / len(shares)
            for user_name in shares:
                if user_name not in users:
                    raise ValueError(f"User '{user_name}' not found")
                expense_splits.append(Split(
                    expense_id="",  # Will be set after expense creation
                    user_id=users[user_name],
                    share_type=split_type,
                    value=share_amount
                ))
        
        elif split_type == SplitType.EXACT:
            for i, user_name in enumerate(shares):
                if user_name not in users:
                    raise ValueError(f"User '{user_name}' not found")
                expense_splits.append(Split(
                    expense_id="",  # Will be set after expense creation
                    user_id=users[user_name],
                    share_type=split_type,
                    value=to_decimal(amount)
                ))
        
        elif split_type == SplitType.PERCENT:
            for user_name in shares:
                if user_name not in users:
                    raise ValueError(f"User '{user_name}' not found")
                # Note: In real implementation, we'd parse percentage values
                expense_splits.append(Split(
                    expense_id="",  # Will be set after expense creation
                    user_id=users[user_name],
                    share_type=split_type,
                    value=Decimal('100') / len(shares)  # Simplified equal percentage
                ))
        
        # Create expense
        expense_id = str(uuid.uuid4())[:8]
        expense = Expense(
            id=expense_id,
            group_id=group.id,
            payer_id=users[paid_by],
            amount=to_decimal(amount),
            description=description,
            timestamp=datetime.now(),
            splits=expense_splits
        )
        
        # Set expense_id in splits
        for split in expense.splits:
            split.expense_id = expense_id
        
        self.storage.save_expense(expense)
        print(f"Added expense: {expense}")
        return expense_id
    
    def list_balances(self, group_name: str):
        """List balances for a group."""
        groups = self.storage.load_groups()
        group = next((g for g in groups if g.name == group_name), None)
        if not group:
            raise ValueError(f"Group '{group_name}' not found")
        
        summary = self.ledger_service.get_group_summary(group.id)
        users = {user.id: user.name for user in self.storage.load_users()}
        
        print(f"\n=== Balances for {group_name} ===")
        for user_id, balance in summary['balances'].items():
            user_name = users.get(user_id, user_id)
            if balance > 0:
                print(f"{user_name}: +${balance} (owed to them)")
            elif balance < 0:
                print(f"{user_name}: -${abs(balance)} (owes)")
            else:
                print(f"{user_name}: $0 (even)")
    
    def suggest_settlements(self, group_name: str):
        """Suggest optimal settlements for a group."""
        groups = self.storage.load_groups()
        group = next((g for g in groups if g.name == group_name), None)
        if not group:
            raise ValueError(f"Group '{group_name}' not found")
        
        balances = self.ledger_service.calculate_balances(group.id)
        settlements = self.settlement_service.suggest_settlements(balances)
        users = {user.id: user.name for user in self.storage.load_users()}
        
        print(f"\n=== Settlement Suggestions for {group_name} ===")
        if not settlements:
            print("No settlements needed - everyone is even!")
            return
        
        for settlement in settlements:
            from_name = users.get(settlement['from_user'], settlement['from_user'])
            to_name = users.get(settlement['to_user'], settlement['to_user'])
            print(f"{from_name} → {to_name}: ${settlement['amount']}")
        
        stats = self.settlement_service.calculate_settlement_stats(balances, settlements)
        print(f"\nSummary: {stats['settlement_count']} transactions needed")
    
    def record_payment(self, group_name: str, from_user: str, to_user: str, amount: float):
        """Record a payment between users."""
        groups = self.storage.load_groups()
        group = next((g for g in groups if g.name == group_name), None)
        if not group:
            raise ValueError(f"Group '{group_name}' not found")
        
        users = {user.name: user.id for user in self.storage.load_users()}
        if from_user not in users or to_user not in users:
            raise ValueError("One or both users not found")
        
        payment_id = str(uuid.uuid4())[:8]
        self.storage.save_payment(
            payment_id=payment_id,
            group_id=group.id,
            from_user=users[from_user],
            to_user=users[to_user],
            amount=to_decimal(amount)
        )
        
        print(f"Recorded payment: {from_user} paid {to_user} ${amount}")
    
    def notify_group(self, group_name: str, notification_type: str):
        """Send notifications to group members."""
        groups = self.storage.load_groups()
        group = next((g for g in groups if g.name == group_name), None)
        if not group:
            raise ValueError(f"Group '{group_name}' not found")
        
        users = {user.id: user for user in self.storage.load_users()}
        
        if notification_type == "balances":
            balances = self.ledger_service.calculate_balances(group.id)
            user_names = {user.id: user.name for user in users.values()}
            
            for user_id in group.member_ids:
                user_balances = {}
                for other_id, balance in balances.items():
                    if other_id != user_id:
                        other_name = user_names.get(other_id, other_id)
                        if balance > 0:
                            user_balances[other_name] = f"-${balance}"
                        elif balance < 0:
                            user_balances[other_name] = f"+${abs(balance)}"
                
                self.notification_service.send_balance_update(
                    users[user_id].name, user_balances
                )
        
        elif notification_type == "settlements":
            balances = self.ledger_service.calculate_balances(group.id)
            settlements = self.settlement_service.suggest_settlements(balances)
            user_names = {user.id: user.name for user in users.values()}
            
            for user_id in group.member_ids:
                user_settlements = []
                for settlement in settlements:
                    if settlement['from_user'] == user_id or settlement['to_user'] == user_id:
                        user_settlements.append({
                            'from_user': user_names.get(settlement['from_user'], settlement['from_user']),
                            'to_user': user_names.get(settlement['to_user'], settlement['to_user']),
                            'amount': settlement['amount']
                        })
                
                self.notification_service.send_settlement_suggestion(
                    users[user_id].name, user_settlements
                )
        
        print(f"Sent {notification_type} notifications to {group_name}")


def create_parser():
    """create command-line argument parser."""
    parser = argparse.ArgumentParser(description="CashMates - Expense splitting for roommates")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create user command
    user_parser = subparsers.add_parser('create-user', help='Create a new user')
    user_parser.add_argument('name', help='User name')
    user_parser.add_argument('--phone', help='Phone number')
    
    # Create group command
    group_parser = subparsers.add_parser('create-group', help='Create a new group')
    group_parser.add_argument('group_name', help='Group name')
    group_parser.add_argument('--members', required=True, help='Comma-separated member names')
    
    # Add expense command
    expense_parser = subparsers.add_parser('add-expense', help='Add an expense')
    expense_parser.add_argument('group', help='Group name')
    expense_parser.add_argument('--paid-by', required=True, help='User who paid')
    expense_parser.add_argument('--amount', type=float, required=True, help='Amount paid')
    expense_parser.add_argument('--desc', required=True, help='Expense description')
    expense_parser.add_argument('--split', choices=['equal', 'exact', 'percent'], 
                               default='equal', help='Split type')
    expense_parser.add_argument('--shares', required=True, help='Comma-separated user names')
    
    # List balances command
    balance_parser = subparsers.add_parser('list-balances', help='List group balances')
    balance_parser.add_argument('group', help='Group name')
    
    # Suggest settlements command
    settlement_parser = subparsers.add_parser('suggest-settlements', help='Suggest settlements')
    settlement_parser.add_argument('group', help='Group name')
    
    # Record payment command
    payment_parser = subparsers.add_parser('record-payment', help='Record a payment')
    payment_parser.add_argument('group', help='Group name')
    payment_parser.add_argument('--from', required=True, help='User who paid')
    payment_parser.add_argument('--to', required=True, help='User who received')
    payment_parser.add_argument('--amount', type=float, required=True, help='Payment amount')
    
    # Notify command
    notify_parser = subparsers.add_parser('notify', help='Send notifications')
    notify_parser.add_argument('group', help='Group name')
    notify_parser.add_argument('--what', choices=['balances', 'settlements'], 
                              required=True, help='Notification type')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = CashMatesCLI()
    
    try:
        if args.command == 'create-user':
            cli.create_user(args.name, args.phone)
        
        elif args.command == 'create-group':
            members = [name.strip() for name in args.members.split(',')]
            cli.create_group(args.group_name, members)
        
        elif args.command == 'add-expense':
            shares = [name.strip() for name in args.shares.split(',')]
            cli.add_expense(args.group, args.paid_by, args.amount, 
                          args.desc, args.split, shares)
        
        elif args.command == 'list-balances':
            cli.list_balances(args.group)
        
        elif args.command == 'suggest-settlements':
            cli.suggest_settlements(args.group)
        
        elif args.command == 'record-payment':
            cli.record_payment(args.group, getattr(args, 'from'), args.to, args.amount)
        
        elif args.command == 'notify':
            cli.notify_group(args.group, args.what)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
