from app.services.embedding_service import (
    embedding_service
)

from app.services.milvus_service import (
    milvus_service
)

from app.repositories.document_repo import get_document_by_id



async def semantic_search(
    db,
    query:str,
    limit:int,
    user_id:int
):


    vector = embedding_service.create_embedding(
        query
    )


    results = milvus_service.search(
        vector,
        user_id,
        limit
    )


    output = []

    for item in results:

        document = await get_document_by_id(
            db,
            item["document_id"],
            user_id
        )

        output.append(
            {
                "filename": document.filename if document else None,
                "page": item["page"],
                "chunk": item["chunk"],
                "score": item["score"]
            }
        )


    return output
