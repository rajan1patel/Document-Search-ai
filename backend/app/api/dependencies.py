from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession


from app.database.connection import get_db

from app.core.security import decode_access_token

from app.repositories.user_repo import get_user_by_email

from app.models.user import User



oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)



async def get_current_user(
    token:str = Depends(oauth2_scheme),
    db:AsyncSession = Depends(get_db)
):


    payload = decode_access_token(token)


    if payload is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user_id = payload.get("user_id")


    if user_id is None:

        raise HTTPException(
            401,
            "Invalid token"
        )


    from sqlalchemy import select


    result = await db.execute(
        select(User)
        .where(User.id==user_id)
    )


    user=result.scalar_one_or_none()


    if user is None:

        raise HTTPException(
            401,
            "User not found"
        )


    return user