from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import os
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Atlas connection URL
MONGODB_URL = os.getenv("MONGODB_URI")
if not MONGODB_URL:
    raise ValueError("MONGODB_URI environment variable is not set")

DATABASE_NAME = "expense_splitter"

# Create MongoDB client with SSL/TLS
client = MongoClient(
    MONGODB_URL,
    tls=True,
    tlsAllowInvalidCertificates=False,
    serverSelectionTimeoutMS=5000
)

# Test the connection
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")
    raise

db = client[DATABASE_NAME]

# Collections
expenses_collection = db.expenses
people_collection = db.people
categories_collection = db.categories

# Helper functions for MongoDB operations
def get_db():
    """Get database instance"""
    return db

def convert_id_to_str(data: dict) -> dict:
    """Convert MongoDB ObjectId to string in response"""
    if "_id" in data:
        data["_id"] = str(data["_id"])
    return data

def convert_str_to_id(id_str: str) -> ObjectId:
    """Convert string ID to MongoDB ObjectId"""
    return ObjectId(id_str)

# MongoDB models
class MongoDBModel:
    @classmethod
    def from_dict(cls, data: dict):
        """Convert dictionary to model instance"""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return self.__dict__

# Example usage:
# expense = {
#     "amount": 100.0,
#     "description": "Lunch",
#     "paid_by": "John",
#     "category": "food",
#     "shares": [
#         {
#             "person": "John",
#             "type": "percentage",
#             "value": 50
#         },
#         {
#             "person": "Jane",
#             "type": "percentage",
#             "value": 50
#         }
#     ],
#     "created_at": datetime.utcnow()
# }
# expenses_collection.insert_one(expense) 