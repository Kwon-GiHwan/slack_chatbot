from langchain_community.vectorstores import ElasticsearchStore
from elasticsearch import Elasticsearch
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)

class Elastic:
    def __init__(self, host, port, embedding_model=None, username=None, password=None, index_name="default"):
        """
        Elastic 클래스 초기화.
        :param host: Elasticsearch 호스트 URL
        :param username: Elasticsearch 사용자 이름 (필요 시)
        :param password: Elasticsearch 비밀번호 (필요 시)
        :param index_name: 사용할 Elasticsearch 인덱스 이름
        """
        self.index_name = index_name
        self.es_client = Elasticsearch(
            hosts=[f"{host}"],
            http_auth=(username, password) if username and password else None
        )

        if embedding_model is None:
            raise ValueError("An embedding model must be provided.")
        self.embedding_model = embedding_model

        self.vectorstore = ElasticsearchStore(
            embedding=self.embedding_model,
            es_connection=self.es_client,
            index_name=index_name,
            strategy=ElasticsearchStore.ApproxRetrievalStrategy(
                hybrid=True
            )
        )

        print(f"Connected to Elasticsearch at {host}, using index: {index_name}")#log로 바꾸기

    def remove_duplicate_documents(self,documents):
        """ 리스트에서 중복된 Document 객체를 제거하는 함수 """
        unique_docs = {}

        for doc in documents:
            key = (doc.page_content, doc.metadata.get("title", ""))

            if key not in unique_docs:
                unique_docs[key] = doc

        return list(unique_docs.values())


    def create_document_from_hit(self, hit):
        """ 검색 결과를 Document 객체로 변환 """
        _source = hit["_source"]
        return Document(
            page_content=_source.get("text", ""),
            metadata={
                "title": _source.get("metadata", {}).get("title", ""),
                "created": _source.get("metadata", {}).get("created", ""),
                "updated": _source.get("metadata", {}).get("updated", ""),
                "creator": _source.get("metadata", {}).get("creator", ""),
                "source": _source.get("metadata", {}).get("source", ""),
                "section": _source.get("metadata", {}).get("section", ""),
                "url": _source.get("metadata", {}).get("url", ""),
                "score": hit.get("_score", 0)  # 검색 점수 추가
            }
        )

    def hybrid_search(self, query, k=10, vector_weight=0.5):
        try:
            # 벡터 검색 수행
            vector_query = self.embedding_model.embed_query(query)
            vector_response = self.es_client.search(
                index=self.index_name,
                body={
                    "size": k,
                    "_source": ["vector", "metadata.title", "text", "metadata"],
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                                "params": {"query_vector": vector_query}
                            }
                        }
                    }
                }
            )

            # 키워드 검색 수행
            keyword_response = self.es_client.search(index=self.index_name, body={
                "size": k,
                "_source": ["text", "metadata"],
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["text^3", "metadata.title"],
                        "type": "best_fields"
                    }
                }
            })

            # 결과 결합
            combined_results = {}

            # 벡터 검색 결과 처리
            for hit in vector_response['hits']['hits']:
                doc_id = hit['_id']
                score = hit['_score'] * vector_weight
                combined_results[doc_id] = {
                    'hit': hit,
                    'score': score
                }

            # 키워드 검색 결과 처리
            for hit in keyword_response['hits']['hits']:
                doc_id = hit['_id']
                score = hit['_score'] * (1 - vector_weight)
                if doc_id in combined_results:
                    combined_results[doc_id]['score'] += score
                else:
                    combined_results[doc_id] = {
                        'hit': hit,
                        'score': score
                    }

            # 결과 정렬 및 Document 객체 생성
            sorted_results = sorted(combined_results.items(),
                                    key=lambda x: x[1]['score'],
                                    reverse=True)[:k]

            unique_documents = {}
            documents = []
            for _, result in sorted_results:
                doc = self.create_document_from_hit(result['hit'])
                title = doc.metadata.get("title", "")
                created = doc.metadata.get("created", "")
                key = (title, created)

                if key not in unique_documents:  # 중복 체크
                    unique_documents[key] = doc
                    doc.metadata['final_score'] = result['score']  # 최종 점수 추가
                    documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise

    def similarity_search(self, query, k=10):
        """ 기존 similarity_search를 hybrid_search로 대체 """
        return self.hybrid_search(query, k=k)