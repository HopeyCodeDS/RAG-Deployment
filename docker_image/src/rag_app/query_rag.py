import logging
from dataclasses import dataclass
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
from rag_app.get_chroma_db import get_chroma_db

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
Use this context to answer the question, but respond naturally without referencing the context:

{context}

---

Question: {question}
"""

BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
RELEVANCE_THRESHOLD = 1.0  # ChromaDB L2 distance; lower = more similar

# Module-level singleton — persists across warm Lambda invocations
try:
    _bedrock_model = ChatBedrock(
        model_id=BEDROCK_MODEL_ID,
        region_name="us-east-1",
        model_kwargs={"max_tokens": 1000, "temperature": 0},
    )
except Exception as e:
    logger.error(f"Failed to initialize Bedrock model: {e}")
    _bedrock_model = None


@dataclass
class QueryResponse:
    query_text: str
    response_text: str
    sources: List[str]


def query_rag(query_text: str) -> QueryResponse:
    if _bedrock_model is None:
        raise RuntimeError("Bedrock model is not initialized. Check AWS credentials and configuration.")

    db = get_chroma_db()

    # Search the DB and filter by relevance score
    results = db.similarity_search_with_score(query_text, k=7)
    results = [(doc, score) for doc, score in results if score <= RELEVANCE_THRESHOLD]

    if not results:
        return QueryResponse(
            query_text=query_text,
            response_text="I don't have enough relevant information to answer that question.",
            sources=[],
        )

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    response = _bedrock_model.invoke(prompt)
    response_text = response.content

    sources = [doc.metadata["id"] for doc, _score in results if "id" in doc.metadata]
    logger.info(f"Query: {query_text} | Sources: {sources}")

    return QueryResponse(
        query_text=query_text, response_text=response_text, sources=sources
    )


if __name__ == "__main__":
    query_rag("How can I contact support?")
