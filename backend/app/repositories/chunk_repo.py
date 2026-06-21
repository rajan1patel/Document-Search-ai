from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk



async def create_chunks(
    db:AsyncSession,
    document_id:int,
    chunks:list
):


    objects=[]


    for item in chunks:

        chunk=DocumentChunk(

            document_id=document_id,

            chunk_text=item["text"],

            chunk_index=item["index"]

        )


        objects.append(chunk)



    db.add_all(objects)


    await db.commit()


    return objects