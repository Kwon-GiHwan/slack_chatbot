# Chatbot Project

이 프로젝트는 slack에서 간략한 문서검색용 chatbot으로 활용하기 위해 만들어졌습니다.

## 서비스 흐름

1.  **Slack 메시지 수신**: 사용자가 Slack 채널에 질문을 올리면, FastAPI 서버의 `/slack/events` 엔드포인트가 이를 수신합니다.
2.  **질문 처리**: 수신된 질문은 `Generator` 모듈로 전달됩니다.
3.  **질문 정제**: `Generator`는 LLM(ChatGPT 또는 Gemini)을 사용하여 사용자의 질문을 더 명확하고 검색에 용이한 형태로 정제합니다.
4.  **문서 검색 (Retrieval)**: 정제된 질문을 사용하여 Elasticsearch에서 관련성이 높은 문서를 검색합니다.
5.  **답변 생성 (Generation)**: 검색된 문서를 컨텍스트로 하여 LLM에게 질문에 대한 답변을 생성하도록 요청합니다.
    *   문서의 양이 많을 경우, LLM의 토큰 제한을 고려하여 문서를 여러 청크로 나누어 처리하고, 각 부분적인 답변을 종합하여 최종 답변을 만듭니다.
6.  **Slack 응답**: 생성된 최종 답변을 Slack 채널에 메시지로 전송하여 사용자에게 회신합니다.

## 프로젝트 구성

*   `main.py`: FastAPI 서버를 실행하고 환경 변수를 로드하는 프로젝트의 진입점입니다.
*   `controller/listener.py`: Slack으로부터 오는 이벤트를 수신하고 처리하는 FastAPI 애플리케이션입니다. Slack 요청을 검증하고, 메시지 이벤트를 비동기적으로 처리하여 `Generator`에 전달합니다.
*   `controller/generator.py`: RAG(Retrieval-Augmented Generation)의 핵심 로직을 담당합니다. LLM과 Elasticsearch를 사용하여 질문을 정제하고, 관련 문서를 검색하며, 최종 답변을 생성합니다.
*   `interface/`: 외부 서비스(LLM, Elasticsearch)와의 상호작용을 위한 인터페이스를 정의합니다.
    *   `llm/`: ChatGPT, Gemini 등 다양한 LLM과의 연동을 위한 클래스가 포함되어 있습니다.
    *   `db/`: Elasticsearch 검색을 위한 클래스가 포함되어 있습니다.
    *   `model/`: LLM에 전달할 프롬프트를 생성하는 클래스가 포함되어 있습니다.
*   `setting.env`: API 키, Slack 토큰, Elasticsearch 접속 정보 등 민감한 설정값을 저장하는 파일입니다.
*   `DockerFile`: 애플리케이션을 컨테이너화하기 위한 Docker 설정 파일입니다.
*   `requirements.txt`: 프로젝트에 필요한 Python 패키지 목록입니다.
