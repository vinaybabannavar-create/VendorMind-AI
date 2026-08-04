"""
vectorstore/vendor_store.py

Wraps Qdrant for semantic vendor-profile retrieval. Falls back to a
simple in-memory cosine-similarity store if Qdrant isn't reachable
(e.g. no server configured yet) so the demo never hard-fails.

Embeddings: sentence-transformers (all-MiniLM-L6-v2) — lightweight,
CPU-friendly, no external API dependency for the embedding step itself.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional

_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
_COLLECTION = "vendor_profiles"

_qdrant_client = None
_embed_model = None
_memory_store: List[Dict[str, Any]] = []  # fallback: [{"id":..., "vector":[...], "payload": {...}}]


def _get_embed_model():
    global _embed_model
    if _embed_model is not None:
        return _embed_model
    try:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _embed_model
    except Exception:
        return None


def _fallback_vector(text: str, dim: int = 384) -> List[float]:
    """Deterministic hash-based vector so the pipeline still runs
    (with weaker matching) if sentence-transformers isn't installed."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vec = [(h[i % len(h)] / 255.0) - 0.5 for i in range(dim)]
    return vec


def _embed(text: str) -> List[float]:
    model = _get_embed_model()
    if model is None:
        return _fallback_vector(text)
    try:
        return model.encode(text).tolist()
    except Exception:
        return _fallback_vector(text)


def _get_qdrant():
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        client = QdrantClient(url=_QDRANT_URL, api_key=_QDRANT_API_KEY, timeout=5)
        # Ensure collection exists (idempotent)
        existing = [c.name for c in client.get_collections().collections]
        if _COLLECTION not in existing:
            client.create_collection(
                collection_name=_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        _qdrant_client = client
        return _qdrant_client
    except Exception:
        return None


def upsert_vendor_profile(vendor_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
    """Store/update a vendor's profile embedding."""
    vector = _embed(text)
    payload = {"vendor_id": vendor_id, "text": text, **(metadata or {})}

    client = _get_qdrant()
    if client is not None:
        try:
            from qdrant_client.models import PointStruct
            # Use a stable integer id derived from vendor_id
            point_id = int(hashlib.sha256(vendor_id.encode()).hexdigest()[:12], 16)
            client.upsert(
                collection_name=_COLLECTION,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )
            return
        except Exception:
            pass  # fall through to in-memory store

    _memory_store[:] = [p for p in _memory_store if p["payload"]["vendor_id"] != vendor_id]
    _memory_store.append({"vector": vector, "payload": payload})


def query_similar(text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve the most relevant stored vendor context for a query
    (e.g. RFP criteria text)."""
    vector = _embed(text)

    client = _get_qdrant()
    if client is not None:
        try:
            results = client.search(collection_name=_COLLECTION, query_vector=vector, limit=top_k)
            return [{"score": r.score, **r.payload} for r in results]
        except Exception:
            pass  # fall through to in-memory store

    def _cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb + 1e-8)

    scored = [
        {"score": _cosine(vector, p["vector"]), **p["payload"]}
        for p in _memory_store
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
