import argparse
import os
import sys
import shutil
import logging
from pathlib import Path

from dotenv import load_dotenv

# Loading .env from the same directory as this script
load_dotenv(Path(__file__).resolve().parent / ".env")

# Adding src/ to path so rag_app imports resolve when running from docker_image/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_chroma import Chroma

from rag_app.get_embedding_function import get_embedding_function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_PATH = "src/data/chroma"
DATA_SOURCE_PATH = "src/data/source"


def main():

    # check if the database should be cleared (using the --reset flag)
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)

def load_documents():
    """Load PDF documents using PyPDFDirectoryLoader."""
    if not os.path.isdir(DATA_SOURCE_PATH):
        raise FileNotFoundError(f"Data source directory not found: {DATA_SOURCE_PATH}")
    logger.info(f"📚 Loading documents from: {DATA_SOURCE_PATH}")
    document_loader = PyPDFDirectoryLoader(DATA_SOURCE_PATH)
    return document_loader.load()


def split_documents(documents: list[Document]):
    """Split large documents into smaller chunks for indexing and model context."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the chunk meta-data
        chunk.metadata['id'] = chunk_id
    return chunks


def add_to_chroma(chunks: list[Document]):
    """Store document chunks in ChromaDB, skipping duplicates."""
    try:
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=get_embedding_function()
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise

    # Calculate Page IDs
    chunks_with_ids = calculate_chunk_ids(chunks)
    for chunk in chunks_with_ids:
        print(f"Chunk Page Sample: {chunk.metadata['id']}\n{chunk.page_content}\n\n")

    # Add or update the documents.
    existing_items = db.get(include=[])     # IDs are always included by default
    existing_ids = set(existing_items['ids'])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata['id'] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata['id'] for chunk in new_chunks]
        try:
            db.add_documents(new_chunks, ids=new_chunk_ids)
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise
    else:
        print("✅ No new documents to add")


def clear_database():
    if os.path.exists(CHROMA_PATH):
        try:
            shutil.rmtree(CHROMA_PATH)
        except OSError as e:
            logger.error(f"Failed to clear database: {e}")
            raise


if __name__ == '__main__':
    main()

