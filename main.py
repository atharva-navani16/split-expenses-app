from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict
from decimal import Decimal, ROUND_HALF_UP
import uuid
from datetime import datetime
from collections import defaultdict

app = FastAPI(
    title="Split App Backend",
    description="Backend system for splitting expenses among groups",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
expenses_db = {}
people_db = set()

# Pydantic models
class ExpenseCreate(BaseModel):
    amount: float
    description: str
    paid_by: str
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return round(v, 2)
    
    @validator('description')
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()
    
    @validator('paid_by')
    def validate_paid_by(cls, v):
        if not v or not v.strip():
            raise ValueError('paid_by cannot be empty')
        return v.strip()

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    paid_by: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return round(v, 2) if v is not None else v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Description cannot be empty')
        return v.strip() if v is not None else v
    
    @validator('paid_by')
    def validate_paid_by(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('paid_by cannot be empty')
        return v.strip() if v is not None else v

class Expense(BaseModel):
    id: str
    amount: float
    description: str
    paid_by: str
    created_at: datetime
    updated_at: datetime

class Balance(BaseModel):
    person: str
    total_paid: float
    total_share: float
    balance: float  # positive = owed money, negative = owes money

class Settlement(BaseModel):
    from_person: str
    to_person: str
    amount: float

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    message: str

# Helper functions
def calculate_per_person_share(total_amount: float, num_people: int) -> float:
    """Calculate each person's share, rounded to 2 decimal places"""
    return float(Decimal(str(total_amount / num_people)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def get_balances() -> List[Balance]:
    """Calculate balances for all people"""
    if not expenses_db:
        return []
    
    # Calculate total paid by each person
    total_paid = defaultdict(float)
    total_expenses = 0
    
    for expense in expenses_db.values():
        total_paid[expense['paid_by']] += expense['amount']
        total_expenses += expense['amount']
    
    # Calculate fair share per person
    num_people = len(people_db)
    if num_people == 0:
        return []
    
    fair_share = calculate_per_person_share(total_expenses, num_people)
    
    # Calculate balances
    balances = []
    for person in people_db:
        paid = total_paid.get(person, 0.0)
        balance = paid - fair_share
        balances.append(Balance(
            person=person,
            total_paid=paid,
            total_share=fair_share,
            balance=round(balance, 2)
        ))
    
    return balances

def calculate_settlements() -> List[Settlement]:
    """Calculate optimized settlements to minimize transactions"""
    balances = get_balances()
    
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
        
        if settlement_amount > 0.01:  # Only create settlement if amount is significant
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

# API Endpoints

@app.get("/", response_model=APIResponse)
async def root():
    return APIResponse(
        success=True,
        message="Split App Backend API is running",
        data={"version": "1.0.0", "endpoints": "/docs for API documentation"}
    )

@app.post("/expenses", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_expense(expense: ExpenseCreate):
    try:
        expense_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Add person to people_db
        people_db.add(expense.paid_by)
        
        # Create expense
        new_expense = {
            "id": expense_id,
            "amount": expense.amount,
            "description": expense.description,
            "paid_by": expense.paid_by,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        expenses_db[expense_id] = new_expense
        
        return APIResponse(
            success=True,
            data=new_expense,
            message="Expense added successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/expenses", response_model=APIResponse)
async def get_expenses():
    expenses_list = list(expenses_db.values())
    # Sort by created_at descending
    expenses_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return APIResponse(
        success=True,
        data={"expenses": expenses_list, "count": len(expenses_list)},
        message="Expenses retrieved successfully"
    )

@app.put("/expenses/{expense_id}", response_model=APIResponse)
async def update_expense(expense_id: str, expense_update: ExpenseUpdate):
    if expense_id not in expenses_db:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    try:
        expense = expenses_db[expense_id].copy()
        
        # Update fields if provided
        if expense_update.amount is not None:
            expense['amount'] = expense_update.amount
        if expense_update.description is not None:
            expense['description'] = expense_update.description
        if expense_update.paid_by is not None:
            # Remove old person if no other expenses
            old_paid_by = expense['paid_by']
            expense['paid_by'] = expense_update.paid_by
            people_db.add(expense_update.paid_by)
            
            # Check if old person should be removed
            if old_paid_by != expense_update.paid_by:
                has_other_expenses = any(
                    exp['paid_by'] == old_paid_by and exp['id'] != expense_id
                    for exp in expenses_db.values()
                )
                if not has_other_expenses:
                    people_db.discard(old_paid_by)
        
        expense['updated_at'] = datetime.utcnow().isoformat()
        expenses_db[expense_id] = expense
        
        return APIResponse(
            success=True,
            data=expense,
            message="Expense updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/expenses/{expense_id}", response_model=APIResponse)
async def delete_expense(expense_id: str):
    if expense_id not in expenses_db:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    try:
        expense = expenses_db[expense_id]
        paid_by = expense['paid_by']
        
        # Delete expense
        del expenses_db[expense_id]
        
        # Check if person should be removed
        has_other_expenses = any(exp['paid_by'] == paid_by for exp in expenses_db.values())
        if not has_other_expenses:
            people_db.discard(paid_by)
        
        return APIResponse(
            success=True,
            message="Expense deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/people", response_model=APIResponse)
async def get_people():
    people_list = sorted(list(people_db))
    return APIResponse(
        success=True,
        data={"people": people_list, "count": len(people_list)},
        message="People retrieved successfully"
    )

@app.get("/balances", response_model=APIResponse)
async def get_balances_endpoint():
    balances = get_balances()
    return APIResponse(
        success=True,
        data={"balances": [balance.model_dump() for balance in balances]},
        message="Balances calculated successfully"
    )

@app.get("/settlements", response_model=APIResponse)
async def get_settlements():
    settlements = calculate_settlements()
    return APIResponse(
        success=True,
        data={"settlements": [settlement.model_dump() for settlement in settlements]},
        message="Settlements calculated successfully"
    )

# Initialize with sample data
@app.on_event("startup")
async def startup_event():
    # Add sample expenses for testing
    sample_expenses = [
        {"amount": 600.0, "description": "Dinner at restaurant", "paid_by": "Shantanu"},
        {"amount": 450.0, "description": "Groceries", "paid_by": "Sanket"},
        {"amount": 300.0, "description": "Petrol", "paid_by": "Om"},
        {"amount": 500.0, "description": "Movie Tickets", "paid_by": "Shantanu"},
        {"amount": 280.0, "description": "Pizza", "paid_by": "Sanket"}
    ]
    
    for expense_data in sample_expenses:
        expense_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        people_db.add(expense_data["paid_by"])
        
        expenses_db[expense_id] = {
            "id": expense_id,
            "amount": expense_data["amount"],
            "description": expense_data["description"],
            "paid_by": expense_data["paid_by"],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)