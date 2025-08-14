from abc import ABC, abstractmethod


class LanguageModelInterface(ABC):
    """
    Abstract base class for language model interfaces.
    Defines the common interface for interacting with different models.
    """
    @abstractmethod
    def send_request(self, prompt: str) -> str:
        """
        Sends a prompt to the language model and returns its response.

        Args:
            prompt (str): The input prompt to the model.

        Returns:
            str: The response from the model.
        """
        pass