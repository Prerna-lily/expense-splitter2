from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from .. import models, schemas
from ..schemas import ShareType, Category
from ..database import get_db
from typing import List
from decimal import Decimal
import logging

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={
        400: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse}
    }
)

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Helper function to calculate shares
def calculate_shares(amount: Decimal, shares: List[schemas.ExpenseShare]) -> List[schemas.ExpenseShare]:
    total_percentage = Decimal('0')
    exact_shares = []
    percentage_shares = []
    
    # Separate shares by type
    for share in shares:
        if share.type == schemas.ShareType.EXACT:
            exact_shares.append(share)
        else:
            percentage_shares.append(share)
            total_percentage += share.value
    
    # Calculate exact shares first
    exact_total = Decimal('0')
    for share in exact_shares:
        exact_total += share.value
    
    # Calculate remaining amount for percentage shares
    remaining_amount = Decimal(str(amount)) - exact_total  # Convert float to Decimal
    if remaining_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total exact shares exceed expense amount",
            headers={"X-Error-Code": "400"}
        )
    
    # Calculate percentage shares
    for share in percentage_shares:
        share.value = (share.value / Decimal('100')) * remaining_amount
    
    # Validate total amount
    total_calculated = exact_total + sum(share.value for share in percentage_shares)
    if abs(total_calculated - Decimal(str(amount))) > Decimal('0.01'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculated total ({total_calculated}) does not match expense amount ({amount})",
            headers={"X-Error-Code": "400"}
        )
    
    return shares

# Helper function to get or create person
def get_or_create_person(db: Session, name: str) -> models.Person:
    person = db.query(models.Person).filter(models.Person.name == name).first()
    if not person:
        person = models.Person(name=name)
        db.add(person)
        db.flush()
    return person

# Continue with the rest of the file content...

@router.get("/")
def get_expenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        # Query with joined relationships
        expenses = db.query(models.Expense).options(
            joinedload(models.Expense.paid_by_person),
            joinedload(models.Expense.shares).joinedload(models.ExpenseShare.person)
        ).offset(skip).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        expense_list = []
        for expense in expenses:
            if not expense.paid_by_person:
                continue  # Skip expenses with missing paid_by person
                
            expense_dict = {
                "id": expense.id,
                "amount": float(expense.amount),  # Convert Decimal to float
                "description": expense.description,
                "paid_by": expense.paid_by_person.name,
                "created_at": expense.created_at.isoformat(),
                "shares": [{
                    "person": share.person.name if share.person else "Unknown",
                    "type": share.share_type,
                    "value": float(share.value)  # Convert Decimal to float
                } for share in expense.shares]
            }
            expense_list.append(expense_dict)
        
        return expense_list
    except Exception as e:
        logger.error(f"Error getting expenses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
            headers={"X-Error-Code": "500"}
        )

@router.put("/{expense_id}", response_model=schemas.Expense, operation_id="update_expense_by_id")
def update_expense(expense_id: int, expense_update: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    # Get the expense
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
            headers={"X-Error-Code": "404"}
        )

    # Get or create people
    people = {}
    person_names = set([expense_update.paid_by] + [share.person for share in expense_update.shares])
    
    # First get all existing people
    existing_people = db.query(models.Person).filter(models.Person.name.in_(person_names)).all()
    for person in existing_people:
        people[person.name] = person
    
    # Create new people if needed
    new_people = []
    for person_name in person_names:
        if person_name not in people:
            new_people.append(models.Person(name=person_name))
    
    if new_people:
        db.add_all(new_people)
        db.flush()  # Get IDs for new people
        for person in new_people:
            people[person.name] = person

    # Update expense
    db_expense.amount = Decimal(str(expense_update.amount))
    db_expense.description = expense_update.description
    
    # Get or create category
    category = db.query(models.Category).filter(models.Category.name == expense_update.category.value).first()
    if not category:
        category = models.Category(name=expense_update.category.value)
        db.add(category)
        db.flush()
    db_expense.category_id = category.id
    
    db_expense.paid_by = people[expense_update.paid_by].id

    # Delete existing shares
    db.query(models.ExpenseShare).filter(models.ExpenseShare.expense_id == expense_id).delete()

    # Create new shares
    total_share_value = 0
    for share in expense_update.shares:
        person = people[share.person]
        share_type = share.type
        share_value = share.value
        
        # Store the raw percentage value for percentage shares
        if share_type == "percentage":
            if share_value < 0 or share_value > 100:
                raise HTTPException(
                    status_code=400,
                    detail=f"Percentage value must be between 0 and 100 (got {share_value})",
                    headers={"X-Error-Code": "400"}
                )
        else:
            if share_value < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Exact share value must be positive (got {share_value})",
                    headers={"X-Error-Code": "400"}
                )
        
        total_share_value += share_value
        db_share = models.ExpenseShare(
            expense_id=expense_id,
            person_id=person.id,
            share_type=share_type,
            value=share_value
        )
        db.add(db_share)

    # Validate shares
    percentage_shares = [share for share in expense_update.shares if share.type == ShareType.PERCENTAGE]
    exact_shares = [share for share in expense_update.shares if share.type == ShareType.EXACT]
    
    # Validate percentage shares
    total_percentage = sum(share.value for share in percentage_shares)
    if total_percentage != 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total percentage shares must sum to 100 (got {total_percentage})",
            headers={"X-Error-Code": "400"}
        )
    
    # Validate exact shares
    total_exact = sum(share.value for share in exact_shares)
    if exact_shares and total_exact > expense_update.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total exact shares ({total_exact}) cannot exceed expense amount ({expense_update.amount})",
            headers={"X-Error-Code": "400"}
        )

    db.commit()
    db.refresh(db_expense)
    
    # Convert ORM objects to Pydantic models for response
    response_expense = schemas.Expense(
        id=db_expense.id,
        amount=db_expense.amount,
        description=db_expense.description,
        category=db_expense.category.name,
        paid_by=db_expense.paid_by_person.name,
        shares=[
            schemas.ExpenseShare(
                person=share.person.name,
                type=share.share_type,
                value=share.value if share.share_type == ShareType.EXACT else Decimal(str(share.value))
            )
            for share in db_expense.shares
        ],
        created_at=db_expense.created_at
    )
    return response_expense

@router.delete("/{expense_id}", response_model=schemas.Expense, operation_id="delete_expense_by_id")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    # Get the expense
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
            headers={"X-Error-Code": "404"}
        )

    # Delete expense and its shares
    db.query(models.ExpenseShare).filter(models.ExpenseShare.expense_id == expense_id).delete()
    db.delete(db_expense)
    db.commit()
    
    return db_expense

@router.post("/", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    # Get or create people
    people = {}
    person_names = set([expense.paid_by] + [share.person for share in expense.shares])
    
    # First get all existing people
    existing_people = db.query(models.Person).filter(models.Person.name.in_(person_names)).all()
    for person in existing_people:
        people[person.name] = person
    
    # Create new people if needed
    new_people = []
    for person_name in person_names:
        if person_name not in people:
            new_people.append(models.Person(name=person_name))
    
    if new_people:
        db.add_all(new_people)
        db.flush()  # Get IDs for new people
        for person in new_people:
            people[person.name] = person

    # Get or create category
    category = db.query(models.Category).filter(models.Category.name == expense.category.value).first()
    if not category:
        category = models.Category(name=expense.category.value)
        db.add(category)
        db.flush()

    # Create expense
    db_expense = models.Expense(
        amount=Decimal(str(expense.amount)),  # Convert float to Decimal
        description=expense.description,
        paid_by=people[expense.paid_by].id,
        category_id=category.id
    )
    db.add(db_expense)
    db.flush()  # Get expense id before creating shares

    # Create shares
    total_share_value = 0
    for share in expense.shares:
        person = people[share.person]
        share_type = share.type
        share_value = share.value
        
        if share_type == "percentage":
            share_value = (share_value / 100) * expense.amount
        
        total_share_value += share_value
        db_share = models.ExpenseShare(
            expense_id=db_expense.id,
            person_id=person.id,
            share_type=share_type,
            value=share_value
        )
        db.add(db_share)

    # Validate total shares
    if abs(total_share_value - expense.amount) > 0.01:  # Allow small floating point error
        raise HTTPException(
            status_code=400,
            detail="Total share values do not match expense amount"
        )

    db.commit()
    db.refresh(db_expense)
    
    # Convert SQLAlchemy objects to dictionary for response
    response_expense = {
        "id": db_expense.id,
        "amount": db_expense.amount,
        "description": db_expense.description,
        "category": db_expense.category.name,
        "paid_by": db_expense.paid_by_person.name,
        "created_at": db_expense.created_at,
        "shares": calculate_shares(db_expense.amount, expense.shares)
    }
    
    return response_expense

@router.put("/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.commit()
    db.refresh(db_expense)
    
    # Convert SQLAlchemy objects to dictionary for response
    response_expense = {
        "id": db_expense.id,
        "amount": db_expense.amount,
        "description": db_expense.description,
        "paid_by": db_expense.paid_by_person.name,
        "created_at": db_expense.created_at,
        "shares": [{
            "person": share.person.name,
            "type": share.share_type,
            "value": share.value
        } for share in db_expense.shares]
    }
    
    return response_expense

@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
