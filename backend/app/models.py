from sqlalchemy import Column, String, Float, DateTime, Text, Index
from sqlalchemy.sql import func
from .database import Base

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(String, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    paid_by = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_expenses_paid_by', 'paid_by'),
        Index('idx_expenses_created_at', 'created_at'),
    )