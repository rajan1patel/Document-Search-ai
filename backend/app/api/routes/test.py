from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db



router = APIRouter()



@router.get("/db-test")
async def test_db(
    db:AsyncSession = Depends(get_db)
):

    return {
        "database":"connected"
    }