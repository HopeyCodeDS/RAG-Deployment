import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum
from src.rag_app.query_rag import query_rag, QueryResponse


app = FastAPI()
handler = Mangum(app)


class SubmitQueryRequest(BaseModel):
    query_text: str

@app.get("/")
def index():
    return {"Hello": "World"}

@app.post("/submit_query")
async def submit_query_endpoint(request: SubmitQueryRequest) -> QueryResponse:
    try:
        query_response = query_rag(request.query_text)
        return query_response
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = 8000
    print(f"Running on FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="127.0.0.1", port=port)