from enum import Enum

class ResponseSignal(Enum):

    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILURE = "file_upload_failure"
    PROCESSING_SUCCESS = "processing_success"
    PROCESSING_FAILURE = "processing_failure"
    NO_FILES_ERROR = "no_files_error"
    FILE_ID_ERROR = "no_file_with_id"
    PROJECT_NOT_FOUND_ERROR="project_not_found"
    INSERT_INTO_VECTORDB_ERROR="insert_into_vectordb_error"
    INSERT_INTO_VECTORDB_SUCCESS="insert_into_vectordb_success"
    VECTORDB_SEARCH_ERROR = "vectordb_search_error"
    VECTORDB_SEARCH_SUCCESS = "vectordb_search_success"
    RAG_ANSWER_ERROR = "rag_answer_error"
    RAG_ANSWER_SUCCESS = "rag_answer_success"