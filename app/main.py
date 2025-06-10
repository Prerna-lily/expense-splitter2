from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import mongo_expenses
from . import schemas
from .mongodb import client

app = FastAPI(
    title="Expense Splitter API",
    description="API for splitting expenses between people",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API version prefix
app.include_router(
    mongo_expenses.router,
    prefix="/api/v1"
)

@app.get("/")
async def root():
    return {"message": "Welcome to Expense Splitter API"}

@app.on_event("shutdown")
async def shutdown_event():
    client.close()

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"detail": "Not found", "error_code": "404"}

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return {"detail": "Internal server error", "error_code": "500"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
