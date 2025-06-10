import json
import os
from datetime import datetime

# Base URL for the API (update this when deploying)
# Update this with your Render deployment URL
BASE_URL = "https://expense-splitter.onrender.com/api/v1"

# Sample data
test_people = ["Shantanu", "Sanket", "Om"]
test_expenses = [
    {
        "description": "Dinner at Restaurant",
        "amount": 1200.0,
        "paid_by": "Shantanu",
        "shares": [
            {"person": "Shantanu", "type": "percentage", "value": 40},
            {"person": "Sanket", "type": "percentage", "value": 30},
            {"person": "Om", "type": "percentage", "value": 30}
        ]
    },
    {
        "description": "Movie Tickets",
        "amount": 600.0,
        "paid_by": "Sanket",
        "shares": [
            {"person": "Shantanu", "type": "exact", "value": 200},
            {"person": "Sanket", "type": "exact", "value": 200},
            {"person": "Om", "type": "exact", "value": 200}
        ]
    },
    {
        "description": "Groceries",
        "amount": 800.0,
        "paid_by": "Om",
        "shares": [
            {"person": "Shantanu", "type": "percentage", "value": 50},
            {"person": "Sanket", "type": "percentage", "value": 50}
        ]
    }
]

collection = {
    "info": {
        "name": "Expense Splitter API",
        "description": "API endpoints for Expense Splitter application",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "People",
            "item": [
                {
                    "name": "Get All People",
                    "request": {
                        "method": "GET",
                        "header": [],
                        "url": {
                            "raw": f"{BASE_URL}/people",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": ["api", "v1", "people"]
                        }
                    }
                }
            ]
        },
        {
            "name": "Expenses",
            "item": [
                {
                    "name": "Get All Expenses",
                    "request": {
                        "method": "GET",
                        "header": [],
                        "url": {
                            "raw": f"{BASE_URL}/expenses",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": ["api", "v1", "expenses"]
                        }
                    }
                },
                {
                    "name": "Create Expense",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps(test_expenses[0])
                        },
                        "url": {
                            "raw": f"{BASE_URL}/expenses",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": ["api", "v1", "expenses"]
                        }
                    }
                }
            ]
        },
        {
            "name": "Analytics",
            "item": [
                {
                    "name": "Get Settlements",
                    "request": {
                        "method": "GET",
                        "header": [],
                        "url": {
                            "raw": f"{BASE_URL}/analytics/settlements",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": ["api", "v1", "analytics", "settlements"]
                        }
                    }
                },
                {
                    "name": "Get Balances",
                    "request": {
                        "method": "GET",
                        "header": [],
                        "url": {
                            "raw": f"{BASE_URL}/analytics/balances",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": ["api", "v1", "analytics", "balances"]
                        }
                    }
                }
            ]
        }
    ]
}

# Save the collection
collection_file = "postman_collection.json"
with open(collection_file, 'w') as f:
    json.dump(collection, f, indent=2)

print(f"Postman collection generated at: {os.path.abspath(collection_file)}")
