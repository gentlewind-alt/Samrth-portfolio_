"""FastAPI application entry point for the resume CMS prototype.

- Includes the API router defined in `routers.py`.
- Sets up the database tables on startup.
- Runs with `uvicorn app.main:app --reload` from the `backend` directory.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from . import models, dependencies, routers

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Resume CMS API", version="0.1.0")
# Allow all origins for local development – adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Resume CMS API"}

# Include the router with the / prefix (router already defines full paths)
app.include_router(routers.router)

# Mount vectorizer static files to serve background SVGs
vectorizer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vectorizer"))
if os.path.exists(vectorizer_path):
    app.mount("/vectorizer", StaticFiles(directory=vectorizer_path), name="vectorizer")

# Create tables on startup (SQLite for prototype)
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=dependencies.engine)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

