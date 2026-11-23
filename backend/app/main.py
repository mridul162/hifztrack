from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.auth.csrf import CsrfProtectionMiddleware
from app.core.config import settings

app = FastAPI(title="HifzTrack API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.add_middleware(CsrfProtectionMiddleware)
app.include_router(health_router)
app.include_router(auth_router)
