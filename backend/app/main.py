from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.routers import (
    subjects, documents, concepts, tests, attempts, analytics, settings as settings_router, topics
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="ExamLoop: Personalized, source-grounded exam preparation cycle API.",
    version="1.0.0"
)

# Enable CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subjects.router)
app.include_router(documents.router)
app.include_router(topics.router)
app.include_router(concepts.router)
app.include_router(tests.router)
app.include_router(attempts.router)
app.include_router(analytics.router)
app.include_router(settings_router.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "env": settings.app_env,
        "demo_mode": settings.demo_mode
    }
