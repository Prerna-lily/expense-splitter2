from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List

router = APIRouter(
    prefix="/people",
    tags=["people"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Person)
def create_person(person: schemas.PersonCreate, db: Session = Depends(get_db)):
    db_person = models.Person(name=person.name)
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

@router.get("/", response_model=List[schemas.Person])
def get_people(db: Session = Depends(get_db)):
    people = db.query(models.Person).all()
    return people

@router.get("/{person_name}", response_model=schemas.Person)
def get_person(person_name: str, db: Session = Depends(get_db)):
    person = db.query(models.Person).filter(models.Person.name == person_name).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
