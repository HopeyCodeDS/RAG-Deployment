import logging
import os
import shutil
import sys
from pathlib import Path
from langchain_chroma import Chroma

from rag_app.get_embedding_function import get_embedding_function

logger = logging.getLogger(__name__)

# Get the absolute path of the Chroma data directory
current_dir = Path(__file__).resolve().parent
CHROMA_PATH = str(current_dir.parent / "data" / "chroma")
IS_USING_IMAGE_RUNTIME = bool(os.environ.get("IS_USING_IMAGE_RUNTIME", False))
CHROMA_DB_INSTANCE = None  # Singleton instance of ChromaDB


def get_chroma_db():
    global CHROMA_DB_INSTANCE
    if not CHROMA_DB_INSTANCE:

        # In Lambda runtime, I copied ChromaDB to /tmp so it can have write permissions.
        if IS_USING_IMAGE_RUNTIME:
            try:
                __import__("pysqlite3")
                sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
            except ImportError:
                logger.warning("pysqlite3 not available, using default sqlite3")
            copy_chroma_to_tmp()

        try:
            CHROMA_DB_INSTANCE = Chroma(
                persist_directory=get_runtime_chroma_path(),
                embedding_function=get_embedding_function(),
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
        logger.info(f"Init ChromaDB from {get_runtime_chroma_path()}")

    return CHROMA_DB_INSTANCE


def copy_chroma_to_tmp():
    dst_chroma_path = get_runtime_chroma_path()

    if not os.path.exists(dst_chroma_path):
        os.makedirs(dst_chroma_path)

    tmp_contents = os.listdir(dst_chroma_path)
    if len(tmp_contents) == 0:
        logger.info(f"Copying ChromaDB from {CHROMA_PATH} to {dst_chroma_path}")
        os.makedirs(dst_chroma_path, exist_ok=True)
        try:
            shutil.copytree(CHROMA_PATH, dst_chroma_path, dirs_exist_ok=True)
        except (shutil.Error, OSError) as e:
            logger.error(f"Failed to copy ChromaDB to {dst_chroma_path}: {e}")
            raise
    else:
        logger.info(f"ChromaDB already exists in {dst_chroma_path}")


def get_runtime_chroma_path():
    if IS_USING_IMAGE_RUNTIME:
        return f"/tmp/{CHROMA_PATH}"
    else:
        return CHROMA_PATH
