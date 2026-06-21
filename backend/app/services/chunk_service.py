class TextChunker:


    def __init__(
        self,
        chunk_size=1000,
        overlap=200
    ):

        self.chunk_size=chunk_size
        self.overlap=overlap



    def split(
        self,
        text:str
    ):

        chunks=[]


        start=0

        index=0


        while start < len(text):


            end = start + self.chunk_size


            chunk=text[start:end]


            chunks.append(
                {
                    "text":chunk,
                    "index":index
                }
            )


            index += 1


            start = end - self.overlap



        return chunks



chunker = TextChunker()