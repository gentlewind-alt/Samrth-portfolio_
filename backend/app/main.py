"""FastAPI application for backend-driven portfolio."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .database import engine
from .models import Base
from .routers import portfolio, admin

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="Portfolio API",
    description="Backend-driven portfolio with resume management",
    version="2.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolio.router)
app.include_router(admin.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Portfolio API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
