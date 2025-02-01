from pathlib import Path
from langchain_community.vectorstores import Chroma
from .get_embedding_function import get_embedding_function

# Get the absolute path of the Chroma data directory
current_dir = Path(__file__).resolve().parent
CHROMA_PATH = str(current_dir.parent / "data" / "chroma")
CHROMA_DB_INSTANCE = None       # A reference to singleton instance of ChromaDB


def get_chroma_db():
    global CHROMA_DB_INSTANCE
    if not CHROMA_DB_INSTANCE:
        # prepare the DB
        CHROMA_DB_INSTANCE = Chroma(
            persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function(),
        )
        print(f"✅ Init ChromaDB {CHROMA_DB_INSTANCE} from {CHROMA_PATH}")

    return CHROMA_DB_INSTANCE

print(f"ChromaDB path: {CHROMA_PATH}")