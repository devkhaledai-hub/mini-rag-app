from ...LLMInterface import LLMInterface
from openai import OpenAI, OpenAIError
from ...LLMEnums import OpenAIEnums
import json
import logging
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urlunparse
from typing import List, Union
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
            base_url=self.api_url if self.api_url and len(self.api_url) > 0 else None
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
        chat_history: list = None,
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
        chat_history = chat_history if chat_history is not None else []

        chat_history.append(
            self.construct_prompt(
                prompt=prompt, 
                role=OpenAIEnums.USER.value
                ))

        if self._is_ollama_api_url():
            return self._generate_text_with_ollama_native(
                chat_history=chat_history,
                max_output_tokens=max_output_tokens,
                temperature=temperature
            )
        
        try:
            response = self.client.chat.completions.create(
                model=self.generate_model_id,
                messages=chat_history,
                max_tokens=max_output_tokens,
                temperature=temperature
            )
        except OpenAIError as exc:
            self.logger.error("OpenAI generation request failed: %s", exc)
            return None

        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("No valid response received from OpenAI API.")
            return None

        content = response.choices[0].message.content
        if not content:
            self.logger.error("OpenAI generation returned an empty message content.")
            return None

        return content


    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        
        if isinstance(text, str):
            text = [text]

        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set.")
            return None
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model_id
            )
        except OpenAIError as exc:
            self.logger.error("OpenAI embedding request failed: %s", exc)
            return None

        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("No embedding data received from OpenAI API.")
            return None
        
        return [rec.embedding for rec in response.data]


    def construct_prompt(self, prompt: str, role:str):
        return {
            "role": role,
            "content": prompt,
        }

    def _is_ollama_api_url(self):
        if not self.api_url:
            return False

        parsed_url = urlparse(self.api_url)
        return parsed_url.hostname in ("localhost", "127.0.0.1") and parsed_url.port == 11434

    def _get_ollama_base_url(self):
        parsed_url = urlparse(self.api_url)
        return urlunparse((parsed_url.scheme, parsed_url.netloc, "", "", "", ""))

    def _generate_text_with_ollama_native(self, chat_history: list, max_output_tokens: int, temperature: float):
        payload = {
            "model": self.generate_model_id,
            "messages": chat_history,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": max_output_tokens,
                "temperature": temperature,
            }
        }

        body = json.dumps(payload).encode("utf-8")
        request = urlrequest.Request(
            f"{self._get_ollama_base_url()}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(request, timeout=120) as response:
                response_body = response.read().decode("utf-8")
                response_data = json.loads(response_body)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.logger.error("Ollama generation request failed: %s", exc)
            return None

        message = response_data.get("message", {})
        content = message.get("content")
        if not content:
            self.logger.error("Ollama generation returned an empty message content.")
            return None

        return content



