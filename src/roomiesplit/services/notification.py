"""notification service with twilio integration."""

import os
from abc import ABC, abstractmethod
from typing import Dict, List

from dotenv import load_dotenv

# load environment variables
load_dotenv()


class NotificationService(ABC):
    """abstract notification service interface."""
    
    @abstractmethod
    def send_balance_update(self, user_id: str, balances: Dict[str, str]) -> bool:
        """send balance update notification."""
        pass
    
    @abstractmethod
    def send_settlement_suggestion(self, user_id: str, settlements: List[Dict]) -> bool:
        """send settlement suggestion notification."""
        pass


class TwilioNotificationService(NotificationService):
    """twilio-based notification service (stub implementation)."""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
        self.dry_run = os.getenv('DRY_RUN', '1') == '1'
        
        # in a real implementation, we would initialize the twilio client here
        # self.client = Client(self.account_sid, self.auth_token)
    
    def send_balance_update(self, user_id: str, balances: Dict[str, str]) -> bool:
        """send balance update notification (stub)."""
        message = f"Balance Update for {user_id}:\n"
        for other_user, balance in balances.items():
            if balance.startswith('+'):
                message += f"You owe {other_user}: {balance}\n"
            elif balance.startswith('-'):
                message += f"{other_user} owes you: {balance}\n"
        
        return self._send_message(user_id, message)
    
    def send_settlement_suggestion(self, user_id: str, settlements: List[Dict]) -> bool:
        """send settlement suggestion notification (stub)."""
        message = f"Settlement suggestions for {user_id}:\n"
        for settlement in settlements:
            if settlement['from_user'] == user_id:
                message += f"Pay {settlement['to_user']}: ${settlement['amount']}\n"
            elif settlement['to_user'] == user_id:
                message += f"Receive from {settlement['from_user']}: ${settlement['amount']}\n"
        
        return self._send_message(user_id, message)
    
    def _send_message(self, user_id: str, message: str) -> bool:
        """send message via twilio (stub implementation)."""
        if self.dry_run:
            print(f"[DRY RUN] SMS to {user_id}:")
            print(f"  {message}")
            return True
        
        # in a real implementation:
        # try:
        #     message_obj = self.client.messages.create(
        #         body=message,
        #         from_=self.from_number,
        #         to=user_phone_number
        #     )
        #     return True
        # except Exception as e:
        #     print(f"failed to send sms: {e}")
        #     return False
        
        print(f"[SMS STUB] Would send to {user_id}:")
        print(f"  {message}")
        return True


class ConsoleNotificationService(NotificationService):
    """console-based notification service for testing."""
    
    def send_balance_update(self, user_id: str, balances: Dict[str, str]) -> bool:
        """print balance update to console."""
        print(f"\n=== Balance Update for {user_id} ===")
        for other_user, balance in balances.items():
            print(f"{other_user}: {balance}")
        return True
    
    def send_settlement_suggestion(self, user_id: str, settlements: List[Dict]) -> bool:
        """print settlement suggestions to console."""
        print(f"\n=== Settlement Suggestions for {user_id} ===")
        for settlement in settlements:
            if settlement['from_user'] == user_id:
                print(f"Pay {settlement['to_user']}: ${settlement['amount']}")
            elif settlement['to_user'] == user_id:
                print(f"Receive from {settlement['from_user']}: ${settlement['amount']}")
        return True
