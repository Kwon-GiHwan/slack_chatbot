class Prompt:

    def __init__(self, user_question: str):
        self.user_question = user_question
        self.documents = []

    def add_document(self, document: str, metadata:dict):
        # if len(self.documents) < self.max_documents:
        self.documents.append((document, metadata))
        # else:
            # raise ValueError(f"Cannot add more than {self.max_documents} documents.")

    def generate_prompt_rag(self) -> str:
        prompt_template = """
            당신은 제공된 문서만을 사용하여 질문에 답변하는 지능형 어시스턴트입니다.
            
            **지침:**  
            1. 사용자의 질문 언어와 관계없이, **모든 답변은 한국어로만 작성**합니다.  
            2. 질문과 관련 있는 문서만 사용하여 답변을 생성합니다.  
               - 관련 없는 문서는 **완전히 무시**합니다.  
            3. 제공된 문서에서 **명확한 답을 찾을 수 있는 경우**, 이를 기반으로 답변합니다.  
            4. 만약 요청한 정보가 문서에서 **명확히 제공되지 않은 경우**, 다음과 같이 응답합니다:  
               - **"요청한 정보는 제공된 문서에서 찾을 수 없습니다."**  
            5. 질문이 제공된 문서와 **전혀 관련이 없을 경우**, 다음과 같이 응답합니다:  
               - **"제공된 문서를 기반으로만 답변할 수 있습니다."**  
            6. **외부 지식이나 추론을 하지 않고**, 오직 문서에 포함된 정보만 사용합니다.  
            7. 명확하고 구조적인 답변을 제공합니다.
            8. 사용자에게는 답변만 제공하도록 합니다
            
            ---
            
            ### **사용자의 질문:**  
            {user_question}
            
            ### **관련 문서:**  
            (제공된 문서  중 관련 있는 문서만 필터링)
            {documents}
            
            ### **답변:**  
            (관련 문서에서 정보를 추출하여 **한국어로 구조적인 답변을 작성**, 문서의 메타데이터 및 링크 또한 정리하여 포함할 것, 링크 주소는 가공하지 않고 있는 그대로 출력할것)
                            

"""

        documents_section = "\n".join(
            [f"Document {i+1}: Metadata: {metadata} Content:\"\"\" \n{doc}\n \"\"\"" for i, (doc, metadata) in enumerate(self.documents)]
        )
        answer =  prompt_template.format(
            user_question=self.user_question,
            documents=documents_section or "No documents provided."
        )

        return answer

    def generate_prompt_question(self) -> str:
        prompt_template = """
            당신은 정보 검색을 위한 검색 질의를 최적화하는 전문가입니다. 사용자의 질문을 보다 효과적인 검색 질의로 변환하세요.
            
            ### 가이드라인:
            1. **질문을 진술형 문장으로 변환** (예: "X의 위험 요소는?" → "X의 위험 요소").
            2. **불필요한 단어 제거**, 포함:
               - **일반적인 검색 요청:** "문서를 찾아줘", "검색해 줘", "알려줘", "보여줘", "관련 정보를 찾아줘", "관련된 정보를 찾아줘"
               - **정중한 표현:** "혹시", "부탁해", "궁금합니다"
               - **기간에 대한 표현:** "3개월", "오늘", "지난달"
               - **문서 작성에 대한 표현:** "발생한", "작성된", "쓴"
               - **문서 소스에 대한 단어:** "confluence", "컨플루언스", "jira", "지라", "slack", "슬랙"
            3. **핵심 개념을 우선하며 맥락을 유지**
            4. **전문 용어나 도메인 관련 키워드는 유지**
            5. **추가적인 설명 없이 최적화된 검색 질의만 출력**
            
            ### 예시:
            
            #### 예시 1 (한국어)
            **입력:**  
            *"사이버 보안 관련 문서를 찾아줘"*  
            **출력:**  
            *"사이버 보안"*
            
            #### 예시 2 (영어)
            **입력:**  
            *"Could you find documents about quantum computing?"*  
            **출력:**  
            *"quantum computing"*
            
            ### 변환할 입력:
            **입력:**  
            "{user_question}"  
            **출력:**
            """


        self.user_question = prompt_template.format(
            user_question=self.user_question,
        )

        return self.user_question