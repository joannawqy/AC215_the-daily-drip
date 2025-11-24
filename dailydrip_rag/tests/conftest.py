"""Shared pytest fixtures for the DailyDrip RAG test suite."""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_sentence_transformer_embedding():
    """
    Avoid importing heavy sentence_transformers during tests.
    
    The FastAPI service bootstraps a SentenceTransformer embedding to talk to ChromaDB.
    We stub the embedding function globally so unit/integration tests don't need the real package.
    """
    with patch(
        "src.service.embedding_functions.SentenceTransformerEmbeddingFunction",
        return_value=MagicMock(name="embedding_function"),
    ) as mock:
        yield mock
