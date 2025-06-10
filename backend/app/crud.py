from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import uuid

from .models import Expense
from .schemas import ExpenseCreate, ExpenseUpdate, Balance, Settlement

def get_expense(db: Session, expense_id: str) -> Optional[Expense]:
    """Get expense by ID"""
    return db.query(Expense).filter(Expense.id == expense_id).first()

def get_expenses(db: Session, skip: int = 0, limit: int = 100) -> List[Expense]:
    """Get all expenses"""
    return db.query(Expense).order_by(desc(Expense.created_at)).offset(skip).limit(limit).all()

def create_expense(db: Session, expense: ExpenseCreate) -> Expense:
    """Create new expense"""
    expense_id = str(uuid.uuid4())
    db_expense = Expense(
        id=expense_id,
        amount=expense.amount,
        description=expense.description,
        paid_by=expense.paid_by
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def update_expense(db: Session, expense_id: str, expense_update: ExpenseUpdate) -> Optional[Expense]:
    """Update expense"""
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None
    
    update_data = expense_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_expense, field, value)
    
    db.commit()
    db.refresh(db_expense)
    return db_expense

def delete_expense(db: Session, expense_id: str) -> bool:
    """Delete expense"""
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return False
    
    db.delete(db_expense)
    db.commit()
    return True

def get_all_people(db: Session) -> List[str]:
    """Get all unique people from expenses"""
    people = db.query(Expense.paid_by).distinct().all()
    return sorted([person[0] for person in people])

def calculate_per_person_share(total_amount: float, num_people: int) -> float:
    """Calculate each person's share, rounded to 2 decimal places"""
    if num_people == 0:
        return 0.0
    return float(Decimal(str(total_amount / num_people)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def get_balances(db: Session) -> List[Balance]:
    """Calculate balances for all people"""
    expenses = get_expenses(db)
    
    if not expenses:
        return []
    
    # Calculate total paid by each person
    total_paid = defaultdict(float)
    total_expenses = 0
    
    for expense in expenses:
        total_paid[expense.paid_by] += expense.amount
        total_expenses += expense.amount
    
    # Get all unique people
    people = get_all_people(db)
    num_people = len(people)
    
    if num_people == 0:
        return []
    
    fair_share = calculate_per_person_share(total_expenses, num_people)
    
    # Calculate balances
    balances = []
    for person in people:
        paid = total_paid.get(person, 0.0)
        balance = paid - fair_share
        balances.append(Balance(
            person=person,
            total_paid=paid,
            total_share=fair_share,
            balance=round(balance, 2)
        ))
    
    return balances

def calculate_settlements(db: Session) -> List[Settlement]:
    """Calculate optimized settlements to minimize transactions"""
    balances = get_balances(db)
    
    if not balances:
        return []
    
    # Separate creditors (positive balance) and debtors (negative balance)
    creditors = [(b.person, b.balance) for b in balances if b.balance > 0.01]
    debtors = [(b.person, -b.balance) for b in balances if b.balance < -0.01]
    
    settlements = []
    
    # Sort creditors and debtors by amount (largest first)
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        creditor, credit_amount = creditors[i]
        debtor, debt_amount = debtors[j]
        
        # Calculate settlement amount
        settlement_amount = min(credit_amount, debt_amount)
        
        if settlement_amount > 0.01:
            settlements.append(Settlement(
                from_person=debtor,
                to_person=creditor,
                amount=round(settlement_amount, 2)
            ))
            
            # Update remaining amounts
            creditors[i] = (creditor, credit_amount - settlement_amount)
            debtors[j] = (debtor, debt_amount - settlement_amount)
        
        # Move to next creditor or debtor
        if creditors[i][1] <= 0.01:
            i += 1
        if debtors[j][1] <= 0.01:
            j += 1
    
    return settlements

def create_sample_data(db: Session):
    """Create sample data if no expenses exist"""
    existing_expenses = db.query(Expense).count()
    
    if existing_expenses == 0:
        sample_expenses = [
            {"amount": 600.0, "description": "Dinner at restaurant", "paid_by": "Shantanu"},
            {"amount": 450.0, "description": "Groceries", "paid_by": "Sanket"},
            {"amount": 300.0, "description": "Petrol", "paid_by": "Om"},
            {"amount": 500.0, "description": "Movie Tickets", "paid_by": "Shantanu"},
            {"amount": 280.0, "description": "Pizza", "paid_by": "Sanket"}
        ]
        
        for expense_data in sample_expenses:
            expense = ExpenseCreate(**expense_data)
            create_expense(db, expense)
        
        print("✅ Sample data created successfully")