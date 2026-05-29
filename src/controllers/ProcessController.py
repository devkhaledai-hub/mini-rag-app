from .BaseController import BaseController
from .ProjectController import ProjectController
import os 
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from models import ProcessingEnum
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

class ProcessController(BaseController):

    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id)

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]
    
    def get_file_loader(self, file_id: str):
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(
            self.project_path, 
            file_id
            )
        if not os.path.exists(file_path):
            return None
        
        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        
        return None
    
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader is None:
            return None, f"Unsupported file type for file_id: {file_id}"
        
        try:
            documents = loader.load()
            return documents, "File loaded successfully"
        except Exception as e:
            return None, f"Error loading file: {str(e)}"
        
    def process_file_content(self, file_content:List, file_id:str, chunk_size: int=100, overlap: int=20):

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=overlap,
            length_function=len
            )
        
        file_content_texts = [
            rec.page_content for rec in file_content
        ]
        file_content_metadata = [
            rec.metadata for rec in file_content
        ]

        chunks = text_splitter.create_documents(file_content_texts, metadatas=file_content_metadata)

        return chunks, "File processed successfully"
