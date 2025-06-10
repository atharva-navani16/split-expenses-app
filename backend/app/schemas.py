from pydantic import BaseModel, validator
from typing import List, Optional, Dict
from datetime import datetime

class ExpenseBase(BaseModel):
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

class ExpenseCreate(ExpenseBase):
    pass

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

class ExpenseResponse(ExpenseBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Balance(BaseModel):
    person: str
    total_paid: float
    total_share: float
    balance: float

class Settlement(BaseModel):
    from_person: str
    to_person: str
    amount: float

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    message: str

class PeopleResponse(BaseModel):
    people: List[str]
    count: int

class ExpensesResponse(BaseModel):
    expenses: List[ExpenseResponse]
    count: int

class BalancesResponse(BaseModel):
    balances: List[Balance]

class SettlementsResponse(BaseModel):
    settlements: List[Settlement]