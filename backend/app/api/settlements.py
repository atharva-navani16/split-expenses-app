from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import APIResponse
from ..crud import calculate_settlements

router = APIRouter()

@router.get("/settlements", response_model=APIResponse)
async def get_settlements(db: Session = Depends(get_db)):
    """Get optimized settlement transactions"""
    settlements = calculate_settlements(db)
    
    return APIResponse(
        success=True,
        data={"settlements": [settlement.dict() for settlement in settlements]},
        message="Settlements calculated successfully"
    )