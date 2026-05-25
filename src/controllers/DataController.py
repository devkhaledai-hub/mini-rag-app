from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import os
import re
class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1024 * 1024  # Convert MB to Bytes

    def validate_uploaded_file(self, file: UploadFile):
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        if file.size > self.app_settings.FILE_MAX_SIZE_MB * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_VALIDATION_SUCCESS.value
    
    def generate_unique_filename(self, original_filename: str, project_id: str):
        
        random_key =  self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_filename(original_filename=original_filename)
        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )
        
        while os.path.exists(new_file_path):
            random_key =  self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_key + "_" + cleaned_file_name
            )

        return new_file_path


    def get_clean_filename(self, original_filename: str):
        
        # Remove any special characters and spaces from the filename
        clean_file_name = re.sub(r'[^a-zA-Z0-9_.-]', '', original_filename.strip())
        
        # Replace spaces with underscores
        clean_file_name = clean_file_name.replace(' ', '_')
        
        return clean_file_name
