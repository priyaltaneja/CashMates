# CashMates

As a student living with friends, I quickly noticed how messy shared expenses can get. One day I would cover groceries, the next someone else would pay for takeout, and another roommate would pick up cleaning supplies. Individually these amounts are small, but they add up fast. We found ourselves constantly doing mental math in group chats and sending redundant $3 or $5 e-transfers back and forth. It was both inefficient and frustrating.

This project was my attempt to translate my frustration for this everyday problem into a tangible solution. I built an  expense-splitting tool that records who paid for what, calculates balances automatically, and suggests the minimum number of transfers needed to settle up. 

## Core Features Include...

- **User Management**: Create and manage all roommates
- **Group Management**: Organize roommates into groups
- **Expense Splitting**: Support for equal, exact, and percentage splits
- **Balance Tracking**: Calculate who owes what to whom 
- **Settlement Optimization**: Determine minimal transactions to settle debts
- **Payment Recording**: Track payments between users
- **Notifications**: Twilio SMS integration (stub implementation) for reminders
- **CSV Persistence**: All data stored in CSV files

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Commands

Create a user:
```bash
python src/roomiesplit/main.py create-user Alice --phone +1234567890
```

Create a group:
```bash
python src/roomiesplit/main.py create-group "Apartment 4B" --members Alice,Bob,Charlie
```

Add an expense:
```bash
python src/roomiesplit/main.py add-expense "Apartment 4B" --paid-by Alice --amount 60.00 --desc "Dinner at restaurant" --split equal --shares Alice,Bob,Charlie
```

List balances:
```bash
python src/roomiesplit/main.py list-balances "Apartment 4B"
```

Suggest settlements:
```bash
python src/roomiesplit/main.py suggest-settlements "Apartment 4B"
```

Record a payment:
```bash
python src/roomiesplit/main.py record-payment "Apartment 4B" --from Bob --to Alice --amount 20.00
```

Send notifications:
```bash
python src/roomiesplit/main.py notify "Apartment 4B" --what balances
```

### Sample Workflow

1. **Setup**:
   ```bash
   python src/roomiesplit/main.py create-user Alice
   python src/roomiesplit/main.py create-user Bob
   python src/roomiesplit/main.py create-group "Roommates" --members Alice,Bob
   ```

2. **Add Expenses**:
   ```bash
   python src/roomiesplit/main.py add-expense "Roommates" --paid-by Alice --amount 40.00 --desc "Groceries" --split equal --shares Alice,Bob
   ```

3. **Check Balances**:
   ```bash
   python src/roomiesplit/main.py list-balances "Roommates"
   ```

4. **Settle Debts**:
   ```bash
   python src/roomiesplit/main.py suggest-settlements "Roommates"
   python src/roomiesplit/main.py record-payment "Roommates" --from Bob --to Alice --amount 20.00
   ```

## Split Types

- **Equal**: Divide expense evenly among all specified users
- **Exact**: Specify exact dollar amounts for each user (must sum to total)
- **Percent**: Specify percentages for each user (must sum to 100%)

## Data Storage

All data is stored in CSV files in the `data/` directory:
- `users.csv`: User information
- `groups.csv`: Group information
- `group_members.csv`: Group membership
- `expenses.csv`: Expense records
- `splits.csv`: Expense split details
- `payments.csv`: Payment records

## Notifications

The application includes a Twilio notification service stub. In dry-run mode (default), notifications are printed to console. To enable real SMS:

1. Create `.env` file with Twilio credentials
2. Set `DRY_RUN=0` in environment
3. Provide valid phone numbers for users

## Testing

Run the test suite:
```bash
pytest tests/
```

Tests cover:
- Split validation (equal/exact/percent)
- Balance calculations
- Settlement optimization
- CSV storage operations
- Notification stubs


## Current Limitations

- No data editing/deletion (append-only)
- Simplified percentage splits (equal distribution)
- Basic settlement algorithm
- No web interface
- No user authentication

## Future Enhancements

- Web interface
- Database backend
- User authentication
- Recurring expenses
- Receipt attachments
- Multi-currency support
