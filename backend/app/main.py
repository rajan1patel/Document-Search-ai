from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.api.routes.test import router
from app.api.routes.auth import router as auth_router
from app.api.routes.user import router as user_router
from app.api.routes.documents import router as document_router
from app.api.routes.search import router as search_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.chat import router as chat_router
from app.api.routes.expert_discovery import router as expert_discovery_router

# ── Logging ─────────────────────────────────
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-30s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Quiet down noisy libs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

app = FastAPI(
    title=settings.APP_NAME
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(router)
app.include_router(document_router)
app.include_router(user_router)
app.include_router(search_router)
app.include_router(dashboard_router)
app.include_router(chat_router)
app.include_router(expert_discovery_router)

@app.get("/")
async def root():

    return {
        "message":"Document Search API running"
    }
