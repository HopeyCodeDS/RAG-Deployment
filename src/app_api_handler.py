import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
from rag_app.query_rag import query_rag, QueryResponse


app = FastAPI()
handler = Mangum(app)


class SubmitQueryRequest(BaseModel):
    query_text: str

@app.get("/")
def index():
    return {"Hello": "World"}

@app.post("/submit_query")
def submit_query_endpoint(request: SubmitQueryRequest) -> QueryResponse:
    query_response = query_rag(request.query_text)
    return query_response


if __name__ == "__main__":
    port = 8000
    print(f"Running on FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="127.0.0.1", port=port)