from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document

from sqlalchemy import select, delete

async def create_document(
    db:AsyncSession,
    data:dict
):

    document = Document(
        **data
    )


    db.add(document)

    await db.commit()

    await db.refresh(document)


    return document

async def get_user_documents(
    db,
    user_id:int
):


    result = await db.execute(

        select(Document)
        .where(
            Document.user_id == user_id
        )
        .order_by(
            Document.created_at.desc()
        )

    )


    return result.scalars().all()





async def get_document_by_id(
    db,
    document_id:int,
    user_id:int
):


    result = await db.execute(

        select(Document)
        .where(
            Document.id == document_id,
            Document.user_id == user_id
        )

    )


    return result.scalar_one_or_none()





async def delete_document(
    db,
    document:Document
):


    await db.delete(document)

    await db.commit()