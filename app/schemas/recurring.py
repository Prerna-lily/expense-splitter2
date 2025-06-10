from pydantic import BaseModel
from typing import Optional
from datetime import date

class RecurringExpenseCreate(BaseModel):
    amount: float
    description: str
    paid_by: int
    shares: list
    frequency: str
    start_date: date
    end_date: Optional[date] = None
