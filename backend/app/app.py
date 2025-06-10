from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from .database import engine, get_db
from .models import Base
from .api import expenses, balances, settlements
from .crud import create_sample_data

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Split App Backend",
    description="Backend system for splitting expenses among groups",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="/app/frontend/static"), name="static")

# Include API routers
app.include_router(expenses.router, prefix="/api", tags=["expenses"])
app.include_router(balances.router, prefix="/api", tags=["balances"])
app.include_router(settlements.router, prefix="/api", tags=["settlements"])

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file"""
    return FileResponse('/app/frontend/index.html')

@app.get("/api/")
async def root():
    return {
        "success": True,
        "message": "Split App Backend API is running",
        "data": {
            "version": "1.0.0",
            "endpoints": {
                "docs": "/api/docs",
                "frontend": "/",
                "expenses": "/api/expenses",
                "balances": "/api/balances",
                "settlements": "/api/settlements"
            }
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize database with sample data"""
    db = next(get_db())
    try:
        create_sample_data(db)
        print("✅ Sample data initialized")
    except Exception as e:
        print(f"⚠️  Sample data initialization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)