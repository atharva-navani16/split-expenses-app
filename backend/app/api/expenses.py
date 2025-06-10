from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, 
    APIResponse, ExpensesResponse, PeopleResponse
)
from ..crud import (
    get_expense, get_expenses, create_expense, 
    update_expense, delete_expense, get_all_people
)

router = APIRouter()

@router.post("/expenses", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Add a new expense"""
    try:
        db_expense = create_expense(db, expense)
        return APIResponse(
            success=True,
            data={
                "id": db_expense.id,
                "amount": db_expense.amount,
                "description": db_expense.description,
                "paid_by": db_expense.paid_by,
                "created_at": db_expense.created_at.isoformat(),
                "updated_at": db_expense.updated_at.isoformat()
            },
            message="Expense added successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/expenses", response_model=APIResponse)
async def get_all_expenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all expenses"""
    expenses = get_expenses(db, skip=skip, limit=limit)
    
    expenses_list = []
    for expense in expenses:
        expenses_list.append({
            "id": expense.id,
            "amount": expense.amount,
            "description": expense.description,
            "paid_by": expense.paid_by,
            "created_at": expense.created_at.isoformat(),
            "updated_at": expense.updated_at.isoformat()
        })
    
    return APIResponse(
        success=True,
        data={"expenses": expenses_list, "count": len(expenses_list)},
        message="Expenses retrieved successfully"
    )

@router.get("/expenses/{expense_id}", response_model=APIResponse)
async def get_expense_by_id(expense_id: str, db: Session = Depends(get_db)):
    """Get expense by ID"""
    expense = get_expense(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return APIResponse(
        success=True,
        data={
            "id": expense.id,
            "amount": expense.amount,
            "description": expense.description,
            "paid_by": expense.paid_by,
            "created_at": expense.created_at.isoformat(),
            "updated_at": expense.updated_at.isoformat()
        },
        message="Expense retrieved successfully"
    )

@router.put("/expenses/{expense_id}", response_model=APIResponse)
async def update_expense_by_id(
    expense_id: str, 
    expense_update: ExpenseUpdate, 
    db: Session = Depends(get_db)
):
    """Update expense by ID"""
    try:
        db_expense = update_expense(db, expense_id, expense_update)
        if not db_expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        return APIResponse(
            success=True,
            data={
                "id": db_expense.id,
                "amount": db_expense.amount,
                "description": db_expense.description,
                "paid_by": db_expense.paid_by,
                "created_at": db_expense.created_at.isoformat(),
                "updated_at": db_expense.updated_at.isoformat()
            },
            message="Expense updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/expenses/{expense_id}", response_model=APIResponse)
async def delete_expense_by_id(expense_id: str, db: Session = Depends(get_db)):
    """Delete expense by ID"""
    success = delete_expense(db, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return APIResponse(
        success=True,
        message="Expense deleted successfully"
    )

@router.get("/people", response_model=APIResponse)
async def get_people(db: Session = Depends(get_db)):
    """Get all people"""
    people = get_all_people(db)
    
    return APIResponse(
        success=True,
        data={"people": people, "count": len(people)},
        message="People retrieved successfully"
    )