from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal, InvalidOperation

class ShareType(str, Enum):
    PERCENTAGE = "percentage"
    EXACT = "exact"

class Category(str, Enum):
    FOOD = "food"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"

class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class PersonCreate(PersonBase):
    pass

class Person(PersonBase):
    id: str  # Changed to str for MongoDB ObjectId

    class Config:
        from_attributes = True

class ExpenseShare(BaseModel):
    person: str = Field(..., min_length=1, max_length=100)
    type: ShareType = Field(...)
    value: Decimal = Field(..., ge=0)

    @validator('value')
    def validate_value(cls, v, values):
        if values.get('type') == ShareType.PERCENTAGE and (v < 0 or v > 100):
            raise ValueError('Percentage value must be between 0 and 100')
        return v

class RecurringExpense(BaseModel):
    frequency: Frequency = Field(...)
    start_date: datetime = Field(...)
    end_date: Optional[datetime] = None
    next_occurrence: datetime = Field(...)

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and v < values['start_date']:
            raise ValueError('End date cannot be before start date')
        return v

class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., min_length=1)
    category: Category = Field(...)
    paid_by: str = Field(..., min_length=1)
    shares: List[ExpenseShare] = Field(..., min_items=1)
    recurring: Optional[RecurringExpense] = None

    @validator('shares')
    def validate_shares(cls, v):
        total_percentage = sum(share.value for share in v if share.type == ShareType.PERCENTAGE)
        if total_percentage != 100:
            raise ValueError('Total percentage shares must sum to 100')
        return v

    @validator('recurring')
    def validate_recurring(cls, v, values):
        if v and v.start_date > v.next_occurrence:
            raise ValueError('Start date cannot be after next occurrence')
        if v and v.end_date and v.end_date < v.start_date:
            raise ValueError('End date cannot be before start date')
        return v

class Expense(ExpenseCreate):
    id: str  # Changed to str for MongoDB ObjectId
    created_at: datetime

    class Config:
        from_attributes = True

class Settlement(BaseModel):
    payer: str
    receiver: str
    amount: Decimal = Field(..., ge=0)

class Balance(BaseModel):
    person: str
    balance: Decimal

    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    detail: str
    error_code: str = Field(..., min_length=3, max_length=3)

    class Config:
        from_attributes = True

# Custom error codes
ERROR_CODES = {
    '400': 'BAD_REQUEST',
    '404': 'NOT_FOUND',
    '500': 'INTERNAL_ERROR'
}
