from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    expenses_paid = relationship("Expense", back_populates="paid_by_person")
    expenses_shared = relationship("ExpenseShare", back_populates="person")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    expenses = relationship("Expense", back_populates="category")

from decimal import Decimal

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_by = Column(Integer, ForeignKey("people.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    is_recurring = Column(Boolean, default=False)
    next_occurrence = Column(DateTime, nullable=True)
    
    paid_by_person = relationship("Person", back_populates="expenses_paid")
    category = relationship("Category", back_populates="expenses")
    shares = relationship("ExpenseShare", back_populates="expense")
    recurring = relationship("RecurringExpense", back_populates="expense", uselist=False)

    def __init__(self, amount, **kwargs):
        super().__init__(**kwargs)
        self.amount = Decimal(str(amount))  # Convert float to Decimal

class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    person_id = Column(Integer, ForeignKey("people.id"))
    share_type = Column(String, nullable=False)  # percentage or exact
    value = Column(Float, nullable=False)
    
    expense = relationship("Expense", back_populates="shares")
    person = relationship("Person", back_populates="expenses_shared")

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), unique=True)
    frequency = Column(String, nullable=False)  # daily, weekly, monthly, yearly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    next_occurrence = Column(DateTime, nullable=False)
    
    expense = relationship("Expense", back_populates="recurring")
