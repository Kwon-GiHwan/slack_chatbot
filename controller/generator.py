from typing import List, Union, Generator as TypeGenerator
from langchain.schema import Document
from interface.llm.chatgpt import ChatGPT
from interface.llm.gemini import Gemini
from interface.model.prompt import Prompt
from interface.db.elastic import Elastic
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import time

class Generator:
    """Main generator class for handling RAG-based question answering"""

    def __init__(self, env: dict):
        self.env = env
        self.embedding_model = self._get_embedding_model()
        self.elastic = self._initialize_elastic(self.embedding_model)
        self.llm = self._initialize_llm()
        self.prompt_generator = Prompt(user_question="")

        # LLM 요청당 최대 토큰 제한 설정 (예: 4000 tokens)
        self.max_token_limit = 4000

    def _get_embedding_model(self):
        """Get appropriate embedding model based on LLM type"""
        if self.env["LLM"] == "CHATGPT":
            return OpenAIEmbeddings(api_key=self.env["CHATGPT_API_KEY"])
        elif self.env["LLM"] == "GEMINI":
            return GoogleGenerativeAIEmbeddings(api_key=self.env["GEMINI_API_KEY"])
        raise ValueError(f"Unsupported LLM type: {self.env['LLM']}")

    def _initialize_elastic(self, embedding_model) -> Elastic:
        """Initialize Elasticsearch with embedding model"""
        return Elastic(
            host=self.env["ELASTIC_HOST"],
            port=self.env["ELASTIC_PORT"],
            username=self.env["ELASTIC_USER"],
            password=self.env["ELASTIC_PASSWORD"],
            embedding_model=embedding_model,
            index_name="aitrics"
        )

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration"""
        if self.env["LLM"] == "CHATGPT":
            return ChatGPT(api_key=self.env["CHATGPT_API_KEY"])
        elif self.env["LLM"] == "GEMINI":
            return Gemini(api_key=self.env["GEMINI_API_KEY"])
        raise ValueError(f"Unsupported LLM type: {self.env['LLM']}")

    def _prepare_prompt(self, question: str, context_documents: List[Document]) -> str:
        """Prepare prompt with question and context"""
        self.prompt_generator = Prompt(user_question=question)
        for doc in context_documents:
            self.prompt_generator.add_document(doc.page_content, doc.metadata)
        return self.prompt_generator.generate_prompt_rag()

    def _refine_question(self, question: str) -> str:
        """Prepare prompt with refined question"""
        self.prompt_generator = Prompt(user_question=question)
        return self.prompt_generator.generate_prompt_question()

    def _split_documents(self, documents: List[Document], max_tokens: int = 2000) -> List[List[Document]]:
        """문서들을 토큰 제한을 고려하여 나누는 함수"""
        chunks = []
        current_chunk = []
        current_token_count = 0

        for doc in documents:
            doc_token_count = len(doc.page_content.split())  # 간단한 토큰 개수 추정

            if current_token_count + doc_token_count > max_tokens:
                # 현재 chunk가 max_token을 초과하면 새로운 chunk 시작
                chunks.append(current_chunk)
                current_chunk = []
                current_token_count = 0

            current_chunk.append(doc)
            current_token_count += doc_token_count

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_answer(self, question: str) -> str:
        """Generate an answer using RAG with chunking"""
        try:
            # 질문 다듬기
            question_refined = self._refine_question(question)
            question_refined = self.llm.send_request(question_refined)

            # 유사 문서 검색
            context_documents = self.elastic.similarity_search(question_refined, k=10)

            # 문서를 LLM의 입력 제한을 고려하여 나누기
            document_chunks = self._split_documents(context_documents, max_tokens=self.max_token_limit // 2)

            # 각 문서 청크에 대해 개별적으로 LLM 호출
            partial_answers = []
            for chunk in document_chunks:
                prompt = self._prepare_prompt(question, chunk)
                partial_answer = self.llm.send_request(prompt)
                partial_answers.append(partial_answer)
                time.sleep(2)

            # 최종적인 응답을 생성하기 위해 LLM에 통합 요청
            final_prompt = f"다음은 {question}에 대하여 개별적으로 생성된 응답들입니다:\n\n" + "\n\n".join(partial_answers) + "\n\n이 정보를 종합하고 질문과 메타데이터를 다시 명확하게 판단하여 최종 답변을 생성해 주세요. 링크를 포함해야 합니다."
            final_answer = self.llm.send_request(final_prompt)

            return final_answer

        except Exception as e:
            return f"Error generating answer: {str(e)}"


    def get_streaming_answer(self, question: str) -> TypeGenerator[str, None, None]:
        """Generate a streaming answer using RAG"""
        try:
            context_documents = self.elastic.similarity_search(question, k=5)
            final_prompt = self._prepare_prompt(question, context_documents)
            yield from self.llm.send_request_stream(final_prompt)
        except Exception as e:
            yield f"Error generating answer: {str(e)}"