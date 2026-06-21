from fastapi import APIRouter, Depends

from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

from app.api.dependencies import get_current_user

from app.models.documents import Document

from app.models.user import User



router=APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)



@router.get("")
async def dashboard(

    db:AsyncSession=Depends(get_db),

    user:User=Depends(get_current_user)

):


    result = await db.execute(

        select(
            func.count(Document.id)
        )
        .where(
            Document.user_id==user.id
        )

    )


    count=result.scalar()


    return {

        "total_documents":count,
        "processed_documents":count

    }
