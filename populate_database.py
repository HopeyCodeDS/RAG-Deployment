import argparse
import os
import shutil
import logging

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_chroma import Chroma

from src.rag_app.get_embedding_function import get_embedding_function

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

"""Load: First we need to load our data. This is done with Document Loaders
        (I am making use of PyPDFDirectoryLoader, which will recursively split the document 
        using common separators like new lines until each chunk is the appropriate size.)."""
def load_documents():
    logger.info(f"📚 Loading documents from: {DATA_SOURCE_PATH}")
    document_loader = PyPDFDirectoryLoader(DATA_SOURCE_PATH)
    return document_loader.load()


"""Split: Text splitters break large Documents into smaller chunks. This is useful both for indexing data and passing it into a model, 
           as large chunks are harder to search over and won't fit in a model's finite context window."""
def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
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


"""Store: We need somewhere to store and index our splits, so that they can be searched over later. This is often done using a VectorStore and Embeddings model."""
def add_to_chroma(chunks: list[Document]):
    """ Load the existing database """
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )

    # Calculate Page IDs
    chunks_with_ids = calculate_chunk_ids(chunks)
    for chunk in chunks:
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
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("✅ No new documents to add")


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == '__main__':
    main()

