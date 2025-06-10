import requests
import json
import os

# Read the Postman collection
with open('postman_collection.json', 'r') as f:
    collection = json.load(f)

collection_json = json.dumps(collection, indent=2)

data = {
    "description": "Postman collection for Expense Splitter API",
    "public": True,
    "files": {
        "expense_splitter_api_collection.json": {
            "content": collection_json
        }
    }
}

# Upload to GitHub Gist
response = requests.post(
    "https://api.github.com/gists",
    headers={
        "Accept": "application/vnd.github.v3+json"
    },
    json=data
)

if response.status_code == 201:
    gist_url = response.json()["html_url"]
    print(f"Gist created successfully! URL: {gist_url}")
    print(f"Raw JSON URL: {gist_url}/raw/expense_splitter_api_collection.json")
else:
    print(f"Failed to create Gist. Status code: {response.status_code}")
    print(f"Response: {response.text}")
