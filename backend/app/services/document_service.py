import os
import uuid


from fastapi import HTTPException, UploadFile

from app.repositories.document_repo import (
    get_user_documents,
    get_document_by_id,
    delete_document
)

import os
from app.repositories.document_repo import create_document

from app.services.extractor_service import extractor
from app.services.chunk_service import chunker 
from app.repositories.chunk_repo import create_chunks
from app.services.embedding_service import(embedding_service)
from app.services.milvus_service import (milvus_service)


UPLOAD_DIR="uploads"



ALLOWED_TYPES=[
    "application/pdf",

    "text/plain",

    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]



async def save_document(
    db,
    file:UploadFile,
    user_id:int
):


    if file.content_type not in ALLOWED_TYPES:

        raise HTTPException(
            status_code=400,
            detail="File type not supported"
        )

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    extension=file.filename.split(".")[-1]


    new_name=f"{uuid.uuid4()}.{extension}"


    path=os.path.join(
        UPLOAD_DIR,
        new_name
    )


    content=await file.read()


    with open(path,"wb") as f:

        f.write(content)


    result = extractor.extract(
    path,
    file.content_type)

    document=await create_document(
        db,
        {
            "user_id":user_id,

            "filename":file.filename,

            "file_path":path,

            "file_type":file.content_type,

            "file_size":len(content),
            "extracted_text":result["text"],

            "status":"processing"
        }
    )


    chunks = chunker.split(
    result["text"]
    )


    await create_chunks(
        db,
        document.id,
        chunks
    )

    for chunk in chunks:


        vector = embedding_service.create_embedding(
            chunk["text"]
        )


        milvus_service.insert_vector(
            document.id,
            user_id,
            chunk["text"],
            vector,
            chunk.get("page_number", 0)
        )

    document.status = "completed"
    await db.commit()
    await db.refresh(document)

    return document


async def list_documents(
    db,
    user_id
):

    return await get_user_documents(
        db,
        user_id
    )

async def remove_document(
    db,
    document_id,
    user_id
):


    document = await get_document_by_id(
        db,
        document_id,
        user_id
    )


    if not document:
        raise Exception(
            "Document not found"
        )


    # delete physical file

    if os.path.exists(
        document.file_path
    ):

        os.remove(
            document.file_path
        )

    milvus_service.delete_document_vectors(
        document_id,
        user_id
    )

    await delete_document(
        db,
        document
    )


    return True
