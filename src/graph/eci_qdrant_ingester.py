"""ECI passage ingester: embed page chunks and store in Qdrant.

Run after Qdrant is deployed and port-forwarded:
    QDRANT_HOST=localhost QDRANT_PORT=6333 \
    OPENROUTER_API_KEY=<key> \
    conda run -n edu python src/graph/eci_qdrant_ingester.py

Script is idempotent — re-running overwrites existing points via stable MD5 IDs.
"""
import hashlib
import os
import time
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from graph.eci_passage_chunker import PassageChunk, chunk_all_sections

COLLECTION = "eci_passages"
EMBED_MODEL = "openai/text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 50
SLEEP_BETWEEN_BATCHES = 0.5  # seconds; guards against OpenRouter rate limits


# ── Helpers ───────────────────────────────────────────────────────────────────

def _stable_id(chapter: int, page_num: int) -> int:
    """Deterministic point ID using MD5 — stable across Python processes.

    Do NOT use Python's built-in hash() — it is randomized per process
    by PYTHONHASHSEED and will produce different IDs on every run.
    """
    key = f"{chapter}:{page_num}".encode()
    return int(hashlib.md5(key).hexdigest(), 16) % (2**31)


def ensure_collection(client: QdrantClient) -> None:
    """Create the eci_passages collection if it doesn't already exist."""
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
        print(f"  Created collection '{COLLECTION}' (dim={EMBED_DIM}, cosine)")
    else:
        print(f"  Collection '{COLLECTION}' already exists — will upsert")


def embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed via OpenRouter; fall back to OpenAI direct if rejected."""
    try:
        oc = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        resp = oc.embeddings.create(model=EMBED_MODEL, input=texts)
        return [item.embedding for item in resp.data]
    except Exception as exc:
        print(f"  OpenRouter embedding failed ({exc}), falling back to OpenAI...")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        oc2 = OpenAI(base_url="https://api.openai.com/v1", api_key=openai_key)
        resp2 = oc2.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in resp2.data]


def ingest_all(
    qdrant: QdrantClient,
    chunks: list[PassageChunk],
    api_key: str,
) -> int:
    """Embed all chunks and upsert into Qdrant. Returns total points upserted."""
    ensure_collection(qdrant)
    total = 0

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]

        # Embed the cleaned text (captions instead of filenames)
        vectors = embed_texts([c.content_for_embed for c in batch], api_key)

        points = [
            PointStruct(
                id=_stable_id(c.chapter, c.page_num),
                vector=vec,
                payload={
                    "chapter": c.chapter,
                    "page_num": c.page_num,
                    "section_heading": c.section_heading,
                    "content": c.content,  # absolute image paths for frontend
                },
            )
            for c, vec in zip(batch, vectors)
        ]
        qdrant.upsert(collection_name=COLLECTION, points=points)
        total += len(points)
        print(f"  Upserted {total}/{len(chunks)} points...")

        if batch_start + BATCH_SIZE < len(chunks):
            time.sleep(SLEEP_BETWEEN_BATCHES)

    return total


if __name__ == "__main__":
    # Load .env from project root (two levels above this file: src/graph/ → root)
    from pathlib import Path as _Path
    try:
        from dotenv import load_dotenv
        load_dotenv(_Path(__file__).parent.parent.parent / ".env")
    except ImportError:
        pass  # python-dotenv not installed; fall back to env vars

    qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
    qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
    api_key = os.environ["OPENROUTER_API_KEY"]

    root = Path(__file__).parent.parent.parent
    markdowns = root / "assets" / "ElementsOfCausalInference_sections" / "markdowns"
    toc = markdowns / "01_TOC" / "01_TOC.mmd"

    print("Chunking ECI book sections...")
    chunks = chunk_all_sections(markdowns, toc)
    print(f"Total chunks to ingest: {len(chunks)}")

    print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    n = ingest_all(client, chunks, api_key)
    print(f"\nIngestion complete. {n} points upserted into '{COLLECTION}'.")
