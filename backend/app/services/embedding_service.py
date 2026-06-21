from sentence_transformers import SentenceTransformer



class EmbeddingService:


    def __init__(self):

        self.model = None


    def _get_model(self):

        if self.model is None:

            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

        return self.model



    def create_embedding(
        self,
        text:str
    ):

        vector = self._get_model().encode(
            text
        )

        return vector.tolist()



    def create_many(
        self,
        texts:list[str]
    ):

        vectors=self._get_model().encode(
            texts
        )

        return vectors.tolist()



embedding_service = EmbeddingService()
