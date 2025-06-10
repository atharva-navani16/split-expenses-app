from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import APIResponse
from ..crud import get_balances

router = APIRouter()

@router.get("/balances", response_model=APIResponse)
async def get_balances_endpoint(db: Session = Depends(get_db)):
    """Get current balances for all people"""
    balances = get_balances(db)
    
    return APIResponse(
        success=True,
        data={"balances": [balance.dict() for balance in balances]},
        message="Balances calculated successfully"
    )