from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User


from app.schemas.search import (
    SearchRequest
)


from app.services.search_service import (
    semantic_search
)



router=APIRouter(
    prefix="/search",
    tags=["Search"]
)



@router.post("")
async def search(
    data:SearchRequest,
    db:AsyncSession=Depends(get_db),
    user:User=Depends(get_current_user)
):


    result = await semantic_search(
        db,
        data.query,
        data.limit,
        user.id
    )


    return result
