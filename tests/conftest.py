"""
tests/conftest.py
Shared pytest configuration and fixtures for VendorMind AI test suite.
Stubs heavy ML / cloud dependencies so tests run in lightweight CI environments
(GitHub Actions free runner) without needing PyTorch, CUDA, or GCP credentials.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure the project root is on the Python path for all test modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Stub heavy / cloud-only dependencies before any project imports ───────────

_MOCK_MODULES = [
    # Vector DB & heavy ML packages
    "sentence_transformers",
    "qdrant_client",
    "qdrant_client.http",
    "qdrant_client.http.models",
    # Google Cloud & Vertex AI
    "google.cloud",
    "google.cloud.pubsub_v1",
    "google.cloud.aiplatform",
    "vertexai",
    "vertexai.language_models",
    # OpenTelemetry & ChromaDB
    "opentelemetry",
    "opentelemetry.trace",
    "opentelemetry.sdk",
    "opentelemetry.sdk.trace",
    "chromadb",
]

for _mod in _MOCK_MODULES:
    parts = _mod.split(".")
    for i in range(1, len(parts) + 1):
        _key = ".".join(parts[:i])
        if _key not in sys.modules:
            sys.modules[_key] = MagicMock()
