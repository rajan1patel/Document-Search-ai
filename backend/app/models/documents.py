from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.sql import func

from app.database.base import Base



class Document(Base):

    __tablename__ = "documents"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )


    filename = Column(
        String,
        nullable=False
    )


    file_path = Column(
        String,
        nullable=False
    )


    file_type = Column(
        String
    )


    file_size = Column(
        Integer
    )

    extracted_text = Column(
    String,
    nullable=True
    )

    status = Column(
        String,
        default="uploaded"
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

   