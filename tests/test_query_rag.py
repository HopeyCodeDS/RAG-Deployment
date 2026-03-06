from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def mock_chroma_db():
    """Mock ChromaDB to avoid needing real embeddings."""
    mock_db = MagicMock()
    with patch("rag_app.query_rag.get_chroma_db", return_value=mock_db) as _:
        yield mock_db


@pytest.fixture
def mock_bedrock():
    """Mock the Bedrock model to avoid AWS calls."""
    mock_response = MagicMock()
    mock_response.content = "This is a test response."
    with patch("rag_app.query_rag._bedrock_model") as mock_model:
        mock_model.invoke.return_value = mock_response
        yield mock_model


def _make_doc(page_content, doc_id, score=0.5):
    """Helper to create a mock document with metadata."""
    doc = MagicMock()
    doc.page_content = page_content
    doc.metadata = {"id": doc_id}
    return (doc, score)


def _make_doc_no_id(page_content, score=0.5):
    """Helper to create a mock document without an id in metadata."""
    doc = MagicMock()
    doc.page_content = page_content
    doc.metadata = {}
    return (doc, score)


class TestQueryRag:
    def test_returns_query_response_with_sources(self, mock_chroma_db, mock_bedrock):
        from rag_app.query_rag import query_rag

        mock_chroma_db.similarity_search_with_score.return_value = [
            _make_doc("Galaxy Design offers web development.", "doc:0:0", 0.3),
            _make_doc("Contact us at support@galaxy.com.", "doc:1:0", 0.4),
        ]

        result = query_rag("How can I contact support?")

        assert result.query_text == "How can I contact support?"
        assert result.response_text == "This is a test response."
        assert result.sources == ["doc:0:0", "doc:1:0"]
        mock_bedrock.invoke.assert_called_once()

    def test_filters_low_relevance_results(self, mock_chroma_db, mock_bedrock):
        from rag_app.query_rag import query_rag

        # All results above the relevance threshold (L2 distance > 1.0)
        mock_chroma_db.similarity_search_with_score.return_value = [
            _make_doc("Irrelevant content.", "doc:0:0", 1.5),
            _make_doc("More irrelevant content.", "doc:1:0", 2.0),
        ]

        result = query_rag("What is quantum computing?")

        assert result.response_text == "I don't have enough relevant information to answer that question."
        assert result.sources == []
        mock_bedrock.invoke.assert_not_called()

    def test_empty_search_results(self, mock_chroma_db, mock_bedrock):
        from rag_app.query_rag import query_rag

        mock_chroma_db.similarity_search_with_score.return_value = []

        result = query_rag("Completely unrelated question")

        assert result.response_text == "I don't have enough relevant information to answer that question."
        assert result.sources == []

    def test_query_with_missing_metadata_id(self, mock_chroma_db, mock_bedrock):
        """Docs without 'id' in metadata should be excluded from sources."""
        from rag_app.query_rag import query_rag

        mock_chroma_db.similarity_search_with_score.return_value = [
            _make_doc("Content with id.", "doc:0:0", 0.3),
            _make_doc_no_id("Content without id.", 0.4),
        ]

        result = query_rag("test query")

        assert result.response_text == "This is a test response."
        assert None not in result.sources
        assert result.sources == ["doc:0:0"]

    def test_bedrock_invocation_error(self, mock_chroma_db, mock_bedrock):
        """Bedrock errors should propagate up."""
        from rag_app.query_rag import query_rag

        mock_chroma_db.similarity_search_with_score.return_value = [
            _make_doc("Some content.", "doc:0:0", 0.3),
        ]
        mock_bedrock.invoke.side_effect = Exception("Bedrock timeout")

        with pytest.raises(Exception, match="Bedrock timeout"):
            query_rag("test query")

    def test_chroma_db_error(self, mock_chroma_db, mock_bedrock):
        """ChromaDB errors should propagate up."""
        from rag_app.query_rag import query_rag

        mock_chroma_db.similarity_search_with_score.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            query_rag("test query")


class TestApiEndpoints:
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        # Patch dependencies before importing the app
        with patch("rag_app.query_rag.get_chroma_db"), \
             patch("rag_app.query_rag._bedrock_model"):
            from fastapi.testclient import TestClient
            from app_api_handler import app
            yield TestClient(app)

    def test_health_check(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "rag-api"}

    def test_submit_query_without_api_key_when_configured(self, client):
        with patch("app_api_handler.API_KEY", "test-secret-key"):
            response = client.post(
                "/submit_query",
                json={"query_text": "test question"},
            )
            assert response.status_code == 401

    def test_submit_query_with_valid_api_key(self, client):
        with patch("app_api_handler.API_KEY", "test-secret-key"), \
             patch("rag_app.query_rag.query_rag") as mock_query:
            from rag_app.query_rag import QueryResponse
            mock_query.return_value = QueryResponse(
                query_text="test", response_text="answer", sources=["s1"]
            )
            response = client.post(
                "/submit_query",
                json={"query_text": "test question"},
                headers={"x-api-key": "test-secret-key"},
            )
            assert response.status_code == 200

    def test_submit_query_empty_text(self, client):
        """Empty query text should return 422 validation error."""
        with patch("app_api_handler.API_KEY", None):
            response = client.post("/submit_query", json={"query_text": ""})
            assert response.status_code == 422

    def test_submit_query_whitespace_only(self, client):
        """Whitespace-only query text should return 422 validation error."""
        with patch("app_api_handler.API_KEY", None):
            response = client.post("/submit_query", json={"query_text": "   "})
            assert response.status_code == 422
