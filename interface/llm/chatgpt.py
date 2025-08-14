from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from typing import Generator, List

class ChatGPT:

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.chat = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=0.7,
            streaming=True
        )
        self.memory = ConversationBufferMemory()

    def send_request(self, prompt: str) -> str:
        try:
            messages = [
                # SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=prompt)
            ]
            response = self.chat.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            return f"Error communicating with ChatGPT: {str(e)}"

    def send_request_stream(self, prompt: str) -> Generator:
        try:
            messages = [
                # SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=prompt)
            ]
            response_stream = self.chat.stream(messages)
            for chunk in response_stream:
                yield chunk.content
                
        except Exception as e:
            yield f"Error communicating with ChatGPT: {str(e)}"

    def normalize_question(self, text: str) -> List[str]:
        try:
            messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=text)
            ]
            response = self.chat.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            return f"Error communicating with ChatGPT: {str(e)}"