from fastapi import APIRouter


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
    data:SearchRequest
):


    result = await semantic_search(
        data.query,
        data.limit
    )


    return result
