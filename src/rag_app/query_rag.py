from dataclasses import dataclass
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
from .get_chroma_db import get_chroma_db

PROMPT_TEMPLATE = """
Use this context to answer the question, but respond naturally without referencing the context:

{context}

---

Question: {question}
"""

# BEDROCK_MODEL_ID = "amazon.titan-embed-text-v2:0"
BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

@dataclass
class QueryResponse:
    query_text: str
    response_text: str
    sources: List[str]


def query_rag(query_text: str) -> QueryResponse:
    db = get_chroma_db()

    # Search the DB
    results = db.similarity_search_with_score(query_text, k=3)
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print(prompt)

    model = ChatBedrock(model_id=BEDROCK_MODEL_ID,
                        region_name="us-east-1",
                        model_kwargs={
                            "max_tokens": 1000,
                            "temperature": 0
                        })
    response = model.invoke(prompt)
    response_text = response.content

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    print(f"Response: {response_text}\nSources: {sources}")

    return QueryResponse(
        query_text=query_text, response_text=response_text, sources=sources
    )


if __name__ == "__main__":
    # query_rag("How much does a landing page cost to develop?")
    query_rag("How can I contact support?")
    # while True:
    #     user_query = input("Enter your question (or 'quit' to exit): ")
    #     if user_query.lower() == "quit":
    #         break
    #
    #     try:
    #         response = query_rag(user_query)
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #         continue
