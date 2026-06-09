from ...LLMEnums import CohereEnums, DocumentTypeEnum
from ...LLMInterface import LLMInterface
import cohere
import logging


class CohereProvider(LLMInterface):

    def __init__(
            self, 
            api_key: str, 
            default_input_max_characters: int = 1000, # To prevent sending very large inputs to the API which can lead to timeouts and increased costs.
            default_output_max_tokens: int = 1000, # To control the length of the generated output and manage costs.
            default_generation_temperature: float = 0.1, # To control the creativity of the generated output. Higher values (e.g., 0.8) will make the output more creative, while lower values (e.g., 0.2) will make it more focused and deterministic.
            ):
        
        self.api_key = api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generate_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(api_key=self.api_key)
        self.enums = CohereEnums
        self.logger = logging.getLogger(__name__) # Setting up a logger for the class to log important information and errors. The logger will use the module's name as its identifier.

    def set_generation_model(self, model_id: str): # help me to change the model id while the running of the app without creating a new instance of the provider class
        self.generate_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()
    
    def generate_text(
            self,
            prompt: str,
            chat_history: list = [],
            max_output_tokens: int = None,
            temperature: float = None
        ):

        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        
        if not self.generate_model_id:
            self.logger.error("Generation model ID is not set.")
            return None
        
        response = self.client.chat(
            model=self.generate_model_id,
            message=self.process_text(prompt),
            chat_history=chat_history,
            max_tokens=max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens,
            temperature=temperature if temperature is not None else self.default_generation_temperature
        )

        if not response or not response.text:
            self.logger.error("No response received from Cohere API.")
            return None
        
        return response.text
    

    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set.")
            return None
        
        input_type = CohereEnums.DOCUMENT.value
        if document_type in (DocumentTypeEnum.QUERY, DocumentTypeEnum.QUERY.value):
            input_type = CohereEnums.QUERY.value


        response = self.client.embed(
            model=self.embedding_model_id,
            texts=[text],
            input_type=input_type,
            embedding_types=["float"]
        )

        response_embeddings = getattr(response, "embeddings", None)
        if response is None or response_embeddings is None:
            self.logger.error("No embeddings received from Cohere API.")
            return None

        embeddings = getattr(response_embeddings, "float", None)
        if embeddings is None:
            embeddings_by_type = getattr(response_embeddings, "embeddings", None)
            embeddings = getattr(embeddings_by_type, "float", None)

        if embeddings is None and isinstance(response_embeddings, dict):
            embeddings = response_embeddings.get("float")

        if embeddings is None or len(embeddings) == 0:
            self.logger.error("No embeddings received from Cohere API.")
            return None
        
        return embeddings[0]

    def construct_prompt(self, prompt: str, role:str):
        role = role.value if hasattr(role, "value") else role
        return {
            "role": role,
            "text": prompt,
        }
