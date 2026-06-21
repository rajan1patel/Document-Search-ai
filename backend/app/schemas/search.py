from pydantic import BaseModel



class SearchRequest(BaseModel):

    query:str

    limit:int = 5



class SearchResult(BaseModel):

    document_id:int

    chunk:str

    score:float