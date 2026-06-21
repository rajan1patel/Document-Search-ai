from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends
)


from sqlalchemy.ext.asyncio import AsyncSession


from app.database.connection import get_db

from app.api.dependencies import get_current_user

from app.services.document_service import save_document

from app.models.user import User

from app.services.document_service import (
    get_document_by_id,
    list_documents,
    remove_document
)

from fastapi import HTTPException

router=APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.get("")
async def get_documents(

    db:AsyncSession=Depends(get_db),

    user:User=Depends(get_current_user)

):


    documents = await list_documents(
        db,
        user.id
    )


    return documents

@router.get("/{document_id}")
async def get_document(

    document_id:int,

    db:AsyncSession=Depends(get_db),

    user:User=Depends(get_current_user)

):


    document = await get_document_by_id(
        db,
        document_id,
        user.id
    )


    if not document:

        raise HTTPException(
            404,
            "Document not found"
        )


    return document


@router.delete("/{document_id}")
async def delete_doc(

    document_id:int,

    db:AsyncSession=Depends(get_db),

    user:User=Depends(get_current_user)

):


    await remove_document(
        db,
        document_id,
        user.id
    )


    return {
        "message":
        "Document deleted"
    }


@router.post("/upload")
async def upload_document(
    
    file:UploadFile = File(...),

    db:AsyncSession=Depends(get_db),

    user:User=Depends(get_current_user)

):


    document=await save_document(
        db,
        file,
        user.id
    )


    return document
