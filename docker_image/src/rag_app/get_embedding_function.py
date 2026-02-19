import logging
from langchain_aws import BedrockEmbeddings

logger = logging.getLogger(__name__)


def get_embedding_function():
    try:
        embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name="us-east-1"
        )
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize BedrockEmbeddings: {e}")
        raise
