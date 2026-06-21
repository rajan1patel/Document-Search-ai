from sentence_transformers import SentenceTransformer



class EmbeddingService:


    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )



    def create_embedding(
        self,
        text:str
    ):

        vector = self.model.encode(
            text
        )

        return vector.tolist()



    def create_many(
        self,
        texts:list[str]
    ):

        vectors=self.model.encode(
            texts
        )

        return vectors.tolist()



embedding_service = EmbeddingService()