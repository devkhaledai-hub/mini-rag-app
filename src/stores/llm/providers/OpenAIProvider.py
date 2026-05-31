from ...LLMInterface import LLMInterface
from openai import OpenAI
from ...LLMEnums import OpenAIEnums
import logging

class OpenAIProvider(LLMInterface):

    def __init__(
            self, 
            api_key: str, 
            api_url: str = None,
            default_input_max_characters: int = 1000, # To prevent sending very large inputs to the API which can lead to timeouts and increased costs.
            default_output_max_tokens: int = 1000, # To control the length of the generated output and manage costs.
            default_generation_temperature: float = 0.1, # To control the creativity of the generated output. Higher values (e.g., 0.8) will make the output more creative, while lower values (e.g., 0.2) will make it more focused and deterministic.
            ):
        
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generate_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )
        self.enums = OpenAIEnums
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
            self.logger.error("OpenAI client is not initialized.")
            return None

        if not self.generate_model_id:
            self.logger.error("Generation model ID is not set.")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens
        temperature = temperature if temperature is not None else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(
                prompt=prompt, 
                role=OpenAIEnums.USER.value
                ))
        
        response = self.client.chat.completions.create(
            model=self.generate_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature
        )

        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("No valid response received from OpenAI API.")
            return None
        
        return response.choices[0].message.content


    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set.")
            return None
        
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model_id
        )

        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("No embedding data received from OpenAI API.")
            return None
        
        return response.data[0].embedding


    def construct_prompt(self, prompt: str, role:str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }





