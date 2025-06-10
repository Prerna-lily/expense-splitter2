from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..schemas import RecurringExpense, ExpenseShare
from ..database import get_db
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter(
    prefix="/recurring",
    tags=["recurring"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_recurring_expenses(db: Session = Depends(get_db)):
    recurring_expenses = db.query(models.RecurringExpense).all()
    return [RecurringExpense.from_orm(expense) for expense in recurring_expenses]

@router.get("/due")
def get_due_recurring_expenses(db: Session = Depends(get_db)):
    current_time = datetime.utcnow()
    recurring_expenses = db.query(models.RecurringExpense).filter(
        models.RecurringExpense.next_occurrence <= current_time
    ).all()
    return [RecurringExpense.from_orm(expense) for expense in recurring_expenses]

@router.post("/")
def create_recurring_expense(
    recurring: RecurringExpense,
    db: Session = Depends(get_db)
):
    # Get or create category
    category = db.query(models.Category).filter(models.Category.name == "Recurring").first()
    if not category:
        category = models.Category(name="Recurring")
        db.add(category)
        db.commit()
        db.refresh(category)

    # Create the base expense
    db_expense = models.Expense(
        amount=recurring.amount,
        description=recurring.description,
        paid_by=recurring.paid_by,
        category_id=category.id,
        is_recurring=True
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # Create shares
    for share in recurring.shares:
        db_share = models.ExpenseShare(
            expense_id=db_expense.id,
            person_id=share.person,
            share_type=share.type,
            value=share.value
        )
        db.add(db_share)
    db.commit()

    # Create the recurring expense record
    recurring_record = models.RecurringExpense(
        expense_id=db_expense.id,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        end_date=recurring.end_date,
        next_occurrence=recurring.start_date
    )
    db.add(recurring_record)
    db.commit()
    db.refresh(recurring_record)

    # Convert SQLAlchemy model to Pydantic model
    return RecurringExpense.from_orm(recurring_record)
