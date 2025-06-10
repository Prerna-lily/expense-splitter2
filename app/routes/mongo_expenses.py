from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from decimal import Decimal
from .. import schemas
from ..mongodb import get_db, expenses_collection, people_collection, categories_collection, convert_id_to_str, convert_str_to_id

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={
        400: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse}
    }
)

@router.post("", response_model=schemas.Expense)
async def create_expense(expense: schemas.ExpenseCreate, db=Depends(get_db)):
    # Validate and get people
    people = {}
    person_names = set([expense.paid_by] + [share.person for share in expense.shares])
    
    # Get or create people
    for name in person_names:
        person = people_collection.find_one({"name": name})
        if not person:
            person = {"name": name}
            result = people_collection.insert_one(person)
            person["_id"] = result.inserted_id
        people[name] = person

    # Get or create category
    category = categories_collection.find_one({"name": expense.category.value})
    if not category:
        category = {"name": expense.category.value}
        result = categories_collection.insert_one(category)
        category["_id"] = result.inserted_id

    # Create expense document
    expense_doc = {
        "amount": float(expense.amount),
        "description": expense.description,
        "paid_by": people[expense.paid_by]["_id"],
        "category_id": category["_id"],
        "created_at": datetime.utcnow(),
        "shares": [
            {
                "person_id": people[share.person]["_id"],
                "type": share.type.value,
                "value": float(share.value)
            }
            for share in expense.shares
        ]
    }

    # Insert expense
    result = expenses_collection.insert_one(expense_doc)
    expense_doc["_id"] = result.inserted_id

    # Prepare response
    response = {
        "id": str(expense_doc["_id"]),
        "amount": expense_doc["amount"],
        "description": expense_doc["description"],
        "category": expense.category.value,
        "paid_by": expense.paid_by,
        "created_at": expense_doc["created_at"],
        "shares": [
            {
                "person": share.person,
                "type": share.type.value,
                "value": float(share.value)
            }
            for share in expense.shares
        ]
    }

    return response

@router.get("", response_model=List[schemas.Expense])
async def get_expenses(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    expenses = list(expenses_collection.find().skip(skip).limit(limit))
    
    # Convert to response format
    response = []
    for expense in expenses:
        # Get related data
        paid_by = people_collection.find_one({"_id": expense["paid_by"]})
        category = categories_collection.find_one({"_id": expense["category_id"]})
        
        # Get share details
        shares = []
        for share in expense["shares"]:
            person = people_collection.find_one({"_id": share["person_id"]})
            shares.append({
                "person": person["name"],
                "type": share["type"],
                "value": share["value"]
            })
        
        response.append({
            "id": str(expense["_id"]),
            "amount": expense["amount"],
            "description": expense["description"],
            "category": category["name"],
            "paid_by": paid_by["name"],
            "created_at": expense["created_at"],
            "shares": shares
        })
    
    return response

@router.get("/{expense_id}", response_model=schemas.Expense)
async def get_expense(expense_id: str, db=Depends(get_db)):
    expense = expenses_collection.find_one({"_id": convert_str_to_id(expense_id)})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Get related data
    paid_by = people_collection.find_one({"_id": expense["paid_by"]})
    category = categories_collection.find_one({"_id": expense["category_id"]})
    
    # Get share details
    shares = []
    for share in expense["shares"]:
        person = people_collection.find_one({"_id": share["person_id"]})
        shares.append({
            "person": person["name"],
            "type": share["type"],
            "value": share["value"]
        })
    
    return {
        "id": str(expense["_id"]),
        "amount": expense["amount"],
        "description": expense["description"],
        "category": category["name"],
        "paid_by": paid_by["name"],
        "created_at": expense["created_at"],
        "shares": shares
    }

@router.delete("/{expense_id}")
async def delete_expense(expense_id: str, db=Depends(get_db)):
    result = expenses_collection.delete_one({"_id": convert_str_to_id(expense_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"} 