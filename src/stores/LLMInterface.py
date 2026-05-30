from abc import ABC, abstractmethod

'''
ABC stands for Abstract Base Class. 
It is a module in Python that provides the infrastructure 
for defining abstract base classes.
An abstract base class is a class that cannot be instantiated 
and typically includes one or more abstract methods that must be implemented by any subclass.
'''

class LLMInterface(ABC):

    @abstractmethod # This decorator indicates that the method is abstract and must be implemented by any subclass.
    def set_generation_model(self, model_id: str):
        pass
    
    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int):
        pass

    @abstractmethod
    def generate_text(
        self, 
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None, 
        temperature: float = None ):
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = None):
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role:str):
        pass

