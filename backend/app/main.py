from fastapi import FastAPI

from app.core.config import settings

from app.api.routes.test import router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as user_router
from app.api.routes.documents import router as document_router
from app.api.routes.search import router as search_router
from app.api.routes.dashboard import router as dashboard_router
app = FastAPI(
    title=settings.APP_NAME
)



app.include_router(auth_router)
app.include_router(router)
app.include_router(document_router)
app.include_router(user_router)
app.include_router(search_router)
app.include_router(dashboard_router)

@app.get("/")
async def root():

    return {
        "message":"Document Search API running"
    }