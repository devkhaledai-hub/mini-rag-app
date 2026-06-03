from .LLMEnums import LLMEnums
from .llm.providers import CohereProvider, OpenAIProvider

class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config


    def create(self, provider: str):
        if provider == LLMEnums.OPENAI.value:
            return OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                api_url=self.config.OPENAI_API_URL,
                default_input_max_characters=self.config.INPUT_DEFAULTS_MAX_CHARACTERS,
                default_output_max_tokens=self.config.OUTPUT_DEFAULTS_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DEFAULTS_TEMPERATURE
                )
        if provider == LLMEnums.COHERE.value:
            return CohereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_input_max_characters=self.config.INPUT_DEFAULTS_MAX_CHARACTERS,
                default_output_max_tokens=self.config.OUTPUT_DEFAULTS_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DEFAULTS_TEMPERATURE
            )
        return None
