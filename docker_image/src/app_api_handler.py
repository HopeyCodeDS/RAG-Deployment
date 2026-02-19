import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Loading .env from docker_image/ directory (one level up from src/ directory)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from mangum import Mangum
from rag_app.query_rag import query_rag, QueryResponse

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = Mangum(app)  # This is the entrypoint for AWS Lambda

API_KEY = os.environ.get("API_KEY")


async def verify_api_key(x_api_key: str = Header(default=None)):
    """Verify the API key if one is configured. Skips check when API_KEY env var is unset."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class SubmitQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("query_text", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


@app.get("/")
def index():
    return {"status": "healthy", "service": "rag-api"}


@app.post("/submit_query", dependencies=[Depends(verify_api_key)])
async def submit_query_endpoint(request: SubmitQueryRequest) -> QueryResponse:
    try:
        query_response = query_rag(request.query_text)
        return query_response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again later.")


if __name__ == "__main__":
    port = 8000
    logger.info(f"Running FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="0.0.0.0", port=port)
