import fitz
from docx import Document


# it has one job file-text extraction

class DocumentExtractor:



    def extract_pdf(
        self,
        path:str
    ):

        pdf = fitz.open(path)

        text=""


        for page in pdf:

            text += page.get_text()


        return {
            "text":text,
            "pages":len(pdf)
        }




    def extract_docx(
        self,
        path:str
    ):

        doc = Document(path)


        text=""


        for paragraph in doc.paragraphs:

            text += paragraph.text + "\n"


        return {
            "text":text,
            "pages":None
        }




    def extract_txt(
        self,
        path:str
    ):


        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            text=f.read()


        return {
            "text":text,
            "pages":None
        }




    def extract(
        self,
        path:str,
        file_type:str
    ):


        if "pdf" in file_type:

            return self.extract_pdf(path)


        if "word" in file_type:

            return self.extract_docx(path)


        if "text" in file_type:

            return self.extract_txt(path)



        raise Exception(
            "Unsupported file"
        )



extractor = DocumentExtractor()