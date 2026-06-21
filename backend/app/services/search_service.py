from app.services.embedding_service import (
    embedding_service
)

from app.services.milvus_service import (
    milvus_service
)



async def semantic_search(
    query:str,
    limit:int
):


    vector = embedding_service.create_embedding(
        query
    )


    results = milvus_service.search(
        vector,
        limit
    )


    return results