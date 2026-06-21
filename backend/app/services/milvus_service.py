from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.core.config import settings


class MilvusService:
    def __init__(self):
        self.collection_name = "document_vectors"
        self.collection = None

    def _connect(self):
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=str(settings.MILVUS_PORT),
        )

    def _get_collection(self):
        self._connect()

        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            return self.collection

        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
            ),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="user_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="page_number", dtype=DataType.INT64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        ]

        schema = CollectionSchema(fields)
        self.collection = Collection(self.collection_name, schema)
        self.collection.create_index(
            field_name="embedding",
            index_params={
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            },
        )
        return self.collection

    def insert_vector(self, document_id, user_id, text, vector, page_number=0):
        collection = self._get_collection()
        collection.insert(
            [
                [document_id],
                [user_id],
                [text[:2000]],
                [page_number],
                [vector],
            ]
        )
        collection.flush()

    def search(self, vector, user_id, limit=5):
        collection = self._get_collection()
        collection.load()

        results = collection.search(
            data=[vector],
            anns_field="embedding",
            param={
                "metric_type": "COSINE",
                "params": {"nprobe": 10},
            },
            limit=limit,
            expr=f"user_id == {int(user_id)}",
            output_fields=[
                "document_id",
                "chunk_text",
                "page_number",
            ],
        )

        output = []
        for hits in results:
            for hit in hits:
                output.append(
                    {
                        "document_id": hit.entity.get("document_id"),
                        "page": hit.entity.get("page_number"),
                        "chunk": hit.entity.get("chunk_text"),
                        "score": hit.score,
                    }
                )

        return output

    def delete_document_vectors(self, document_id, user_id):
        collection = self._get_collection()
        collection.delete(
            expr=f"document_id == {int(document_id)} and user_id == {int(user_id)}"
        )
        collection.flush()


milvus_service = MilvusService()
