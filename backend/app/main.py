"""
FastAPI Application Entrypoint for Social Commerce Recommendation Platform.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api.routes import router as api_router
from backend.app.db.connection import get_db, get_db_manager
from backend.app.db.seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database is seeded
    db = get_db()
    if db.posts.count_documents({}) == 0:
        seed_database(force_refresh=True)
    yield


app = FastAPI(
    title="NextGen Social Commerce Recommendation Engine",
    description="End-to-End Recommendation Engine for Social Commerce Feed & Products (Jr. AI Engineer Assignment)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

# Static frontend folder
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "NextGen Recommendation Engine API is running. Visit /docs for OpenAPI documentation."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
