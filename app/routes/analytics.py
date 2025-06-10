from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

@router.get("/health")
def read_health():
    return {"status": "healthy"}


