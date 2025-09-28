"""csv-based storage for data persistence."""

import csv
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models.user import User
from ..models.group import Group
from ..models.expense import Expense, Split
from ..utils.money import to_decimal


class CSVStorage:
    """csv-based storage implementation."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._init_files()
    
    def _init_files(self):
        """initialize csv files with headers if they don't exist."""
        files_config = {
            'users.csv': ['id', 'name', 'phone'],
            'groups.csv': ['id', 'name'],
            'group_members.csv': ['group_id', 'user_id'],
            'expenses.csv': ['id', 'group_id', 'payer_id', 'amount', 'description', 'timestamp'],
            'splits.csv': ['expense_id', 'user_id', 'share_type', 'value'],
            'payments.csv': ['id', 'group_id', 'from_user', 'to_user', 'amount', 'timestamp']
        }
        
        for filename, headers in files_config.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
    
    def _read_csv(self, filename: str) -> List[Dict[str, Any]]:
        """read csv file and return list of dictionaries."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return []
        
        with open(filepath, 'r', newline='') as f:
            return list(csv.DictReader(f))
    
    def _write_csv(self, filename: str, data: List[Dict[str, Any]]):
        """write data to csv file."""
        filepath = self.data_dir / filename
        if not data:
            return
        
        with open(filepath, 'a', newline='') as f:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerows(data)
    
    # user operations
    def save_user(self, user: User):
        """save a user to csv."""
        user_data = {
            'id': user.id,
            'name': user.name,
            'phone': user.phone or ''
        }
        self._write_csv('users.csv', [user_data])
    
    def load_users(self) -> List[User]:
        """load all users from csv."""
        users_data = self._read_csv('users.csv')
        return [
            User(
                id=row['id'],
                name=row['name'],
                phone=row['phone'] if row['phone'] else None
            )
            for row in users_data
        ]
    
    # group operations
    def save_group(self, group: Group):
        """save a group and its members to csv."""
        # save group
        group_data = {
            'id': group.id,
            'name': group.name
        }
        self._write_csv('groups.csv', [group_data])
        
        # save group members
        for user_id in group.member_ids:
            member_data = {
                'group_id': group.id,
                'user_id': user_id
            }
            self._write_csv('group_members.csv', [member_data])
    
    def load_groups(self) -> List[Group]:
        """load all groups and their members from csv."""
        groups_data = self._read_csv('groups.csv')
        members_data = self._read_csv('group_members.csv')
        
        groups = []
        for group_row in groups_data:
            group_id = group_row['id']
            member_ids = {
                row['user_id'] for row in members_data 
                if row['group_id'] == group_id
            }
            groups.append(Group(
                id=group_id,
                name=group_row['name'],
                member_ids=member_ids
            ))
        
        return groups
    
    # Expense operations
    def save_expense(self, expense: Expense):
        """Save an expense and its splits to CSV."""
        # Save expense
        expense_data = {
            'id': expense.id,
            'group_id': expense.group_id,
            'payer_id': expense.payer_id,
            'amount': str(expense.amount),
            'description': expense.description,
            'timestamp': expense.timestamp.isoformat()
        }
        self._write_csv('expenses.csv', [expense_data])
        
        # Save splits
        for split in expense.splits:
            split_data = {
                'expense_id': split.expense_id,
                'user_id': split.user_id,
                'share_type': split.share_type,
                'value': str(split.value)
            }
            self._write_csv('splits.csv', [split_data])
    
    def load_expenses(self) -> List[Expense]:
        """Load all expenses and their splits from CSV."""
        expenses_data = self._read_csv('expenses.csv')
        splits_data = self._read_csv('splits.csv')
        
        expenses = []
        for expense_row in expenses_data:
            expense_id = expense_row['id']
            
            # Get splits for this expense
            expense_splits = [
                Split(
                    expense_id=row['expense_id'],
                    user_id=row['user_id'],
                    share_type=row['share_type'],
                    value=to_decimal(row['value'])
                )
                for row in splits_data if row['expense_id'] == expense_id
            ]
            
            expenses.append(Expense(
                id=expense_id,
                group_id=expense_row['group_id'],
                payer_id=expense_row['payer_id'],
                amount=to_decimal(expense_row['amount']),
                description=expense_row['description'],
                timestamp=datetime.fromisoformat(expense_row['timestamp']),
                splits=expense_splits
            ))
        
        return expenses
    
    # Payment operations
    def save_payment(self, payment_id: str, group_id: str, from_user: str, 
                    to_user: str, amount: Decimal):
        """Save a payment to CSV."""
        payment_data = {
            'id': payment_id,
            'group_id': group_id,
            'from_user': from_user,
            'to_user': to_user,
            'amount': str(amount),
            'timestamp': datetime.now().isoformat()
        }
        self._write_csv('payments.csv', [payment_data])
    
    def load_payments(self) -> List[Dict[str, Any]]:
        """Load all payments from CSV."""
        payments_data = self._read_csv('payments.csv')
        return [
            {
                'id': row['id'],
                'group_id': row['group_id'],
                'from_user': row['from_user'],
                'to_user': row['to_user'],
                'amount': to_decimal(row['amount']),
                'timestamp': datetime.fromisoformat(row['timestamp'])
            }
            for row in payments_data
        ]
