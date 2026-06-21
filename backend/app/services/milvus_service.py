from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)



class MilvusService:


    def __init__(self):

        connections.connect(
            host="localhost",
            port="19530"
        )


        self.collection_name="document_vectors"


        self.create_collection()



    def create_collection(self):


        if utility.has_collection(
            self.collection_name
        ):
            return



        fields=[


            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),



            FieldSchema(
                name="document_id",
                dtype=DataType.INT64
            ),



            FieldSchema(
                name="chunk_text",
                dtype=DataType.VARCHAR,
                max_length=2000
            ),



            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=384
            )
        ]



        schema=CollectionSchema(
            fields
        )


        self.collection=Collection(
            self.collection_name,
            schema
        )

def insert_vector(
    self,
    document_id,
    text,
    vector
):


    data=[

        [document_id],

        [text],

        [vector]

    ]


    self.collection.insert(
        data
    )


def search(
    self,
    vector,
    limit=5
):


    self.collection.load()


    results = self.collection.search(
        data=[vector],
        anns_field="embedding",
        param={
            "metric_type":"COSINE",
            "params":{
                "nprobe":10
            }
        },
        limit=limit,
        output_fields=[
            "document_id",
            "chunk_text"
        ]
    )


    output=[]


    for hits in results:

        for hit in hits:

            output.append(
                {
                "document_id":
                    hit.entity.get(
                        "document_id"
                    ),

                "chunk":
                    hit.entity.get(
                        "chunk_text"
                    ),

                "score":
                    hit.score
                }
            )


    return output

milvus_service = MilvusService()