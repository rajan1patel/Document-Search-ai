from sqlalchemy.ext.asyncio import AsyncSession


from app.repositories.user_repo import (
    get_user_by_email,
    create_user
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)



async def register_user(
    db:AsyncSession,
    email:str,
    password:str
):


    existing = await get_user_by_email(
        db,email
    )


    if existing:
        raise Exception(
            "Email already exists"
        )


    hashed = hash_password(password)


    return await create_user(
        db,
        email,
        hashed
    )




async def login_user(
    db:AsyncSession,
    email:str,
    password:str
):

    user = await get_user_by_email(
        db,email
    )


    if not user:
        raise Exception(
            "Invalid credentials"
        )


    if not verify_password(
        password,
        user.password_hash
    ):
        raise Exception(
            "Invalid credentials"
        )


    token=create_access_token(
        {
          "user_id":user.id
        }
    )


    return token