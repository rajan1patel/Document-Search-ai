from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime
)

from sqlalchemy.sql import func

from app.database.base import Base



class DocumentChunk(Base):

    __tablename__="document_chunks"



    id = Column(
        Integer,
        primary_key=True
    )


    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )


    chunk_text = Column(
        Text,
        nullable=False
    )


    chunk_index = Column(
        Integer,
        nullable=False
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )