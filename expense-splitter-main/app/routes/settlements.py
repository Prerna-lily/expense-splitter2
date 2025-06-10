from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List
import itertools

router = APIRouter(
    prefix="/settlements",
    tags=["settlements"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Settlement])
def get_settlements(db: Session = Depends(get_db)):
    # Get all people and their total expenses
    people = db.query(models.Person).all()
    balances = {person.name: 0.0 for person in people}

    # Calculate balances
    expenses = db.query(models.Expense).all()
    for expense in expenses:
        # Add expense amount to paid_by person's balance
        balances[expense.paid_by_person.name] -= expense.amount
        
        # Add shares to each person's balance
        for share in expense.shares:
            balances[share.person.name] += share.share_value

    # Create simplified settlements
    settlements = []
    # Sort people by balance (most negative first)
    sorted_people = sorted(balances.items(), key=lambda x: x[1])
    
    # Create settlements using a greedy algorithm
    while sorted_people:
        debtor = sorted_people[0]
        creditor = sorted_people[-1]
        
        if debtor[1] >= 0:  # No more debtors
            break
        
        amount = min(abs(debtor[1]), creditor[1])
        settlements.append({
            "payer": debtor[0],
            "receiver": creditor[0],
            "amount": amount
        })
        
        # Update balances
        balances[debtor[0]] += amount
        balances[creditor[0]] -= amount
        
        # Update sorted list
        sorted_people = sorted(balances.items(), key=lambda x: x[1])

    return settlements

@router.get("/balances", response_model=List[schemas.Balance])
def get_balances(db: Session = Depends(get_db)):
    people = db.query(models.Person).all()
    balances = []
    
    for person in people:
        # Calculate total expenses paid by this person
        expenses_paid = sum(
            expense.amount for expense in person.expenses_paid
        )
        
        # Calculate total shares received by this person
        shares_received = sum(
            share.share_value for share in person.expenses_shared
        )
        
        balance = shares_received - expenses_paid
        balances.append({
            "person": person.name,
            "balance": round(balance, 2)
        })

    return balances
