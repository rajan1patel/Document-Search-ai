from fastapi import APIRouter, Depends


from app.models.user import User
from app.api.dependencies import get_current_user



router=APIRouter(
    prefix="/users",
    tags=["Users"]
)



@router.get("/me")
async def get_profile(
    user:User = Depends(get_current_user)
):


    return {
        "id":user.id,
        "email":user.email
    }