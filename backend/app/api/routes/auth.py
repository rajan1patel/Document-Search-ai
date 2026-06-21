from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession


from app.database.connection import get_db

from app.schemas.user import (
    UserCreate,
    UserLogin
)


from app.services.auth_service import (
    register_user,
    login_user
)



router=APIRouter(
    prefix="/auth",
    tags=["Auth"]
)



@router.post("/register")
async def register(
    data:UserCreate,
    db:AsyncSession=Depends(get_db)
):

    try:

        user=await register_user(
            db,
            data.email,
            data.password
        )


        return user


    except Exception as e:

        raise HTTPException(
            400,
            str(e)
        )




@router.post("/login")
async def login(
    data:UserLogin,
    db:AsyncSession=Depends(get_db)
):

    try:

        token=await login_user(
            db,
            data.email,
            data.password
        )


        return {
            "access_token":token,
            "token_type":"bearer"
        }


    except Exception as e:

        raise HTTPException(
            400,
            str(e)
        )