"""Standalone GraphRAG search script — use AFTER ingestion is complete.

Two modes:
  Pure vector search (no graph):
    python scripts/qdrant_search.py "What is the backdoor criterion?" --top-k 3

  Graph-anchored search (true GraphRAG):
    python scripts/qdrant_search.py "What is the backdoor criterion?" \
        --concept backdoor_criterion --top-k 5

With --concept, the script:
  1. Loads src/graph/output/eci_graph.json (no Neo4j needed)
  2. Follows COVERED_IN edges from the concept to Section nodes
  3. Restricts Qdrant search to those sections' page ranges
  4. Falls back to unfiltered global search if no COVERED_IN edges exist

Environment variables
---------------------
QDRANT_HOST        Qdrant server hostname   (default: localhost)
QDRANT_PORT        Qdrant server port       (default: 6333)
QDRANT_PATH        Path to on-disk storage  (overrides host/port if set)
OPENROUTER_API_KEY Required for embedding the query
OPENAI_API_KEY     Fallback if OpenRouter key is missing
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Load .env from project root (scripts/ is one level below root)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed; fall back to shell env vars

COLLECTION = "eci_passages"
EMBED_MODEL = "openai/text-embedding-3-small"
SYNTH_MODEL = "openai/gpt-5-nano"  # lightweight model for synthesis
GRAPH_JSON = Path(__file__).parent.parent / "src" / "graph" / "output" / "eci_graph.json"


# ── Graph helpers ──────────────────────────────────────────────────────────────

def load_graph() -> tuple[dict, list]:
    """Load eci_graph.json → (nodes_by_id, edges)."""
    if not GRAPH_JSON.exists():
        print(f"ERROR: Graph file not found at {GRAPH_JSON}")
        sys.exit(1)
    data = json.loads(GRAPH_JSON.read_text())
    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    return nodes_by_id, data["edges"]


def slugify(text: str) -> str:
    """Normalize a concept name to its graph ID form: lowercase, spaces → underscores."""
    return text.strip().lower().replace(" ", "_").replace("-", "_")


def get_page_ranges(concept_id: str, nodes_by_id: dict, edges: list, window: int = 1) -> tuple[list[tuple[int, int]], str]:
    """Return page ranges and the strategy used.

    Strategy 1 — page_refs (precise): concept node carries exact index pages.
      Each ref becomes [page - window, page + window] to include context.
    Strategy 2 — COVERED_IN (broad): follow edges to Section nodes and use
      their start_page/end_page. Used only when page_refs is absent.

    Returns (ranges, strategy_label).
    """
    node = nodes_by_id.get(concept_id, {})
    page_refs = node.get("page_refs", [])

    if page_refs:
        ranges = [(max(1, p - window), p + window) for p in page_refs]
        return ranges, f"page_refs {page_refs} (±{window} pages)"

    # Fallback: section intervals from COVERED_IN edges
    covered_sections = [
        e["target"] for e in edges
        if e["source"] == concept_id and e["edge_type"] == "COVERED_IN"
    ]
    ranges = []
    for sec_id in covered_sections:
        sec = nodes_by_id.get(sec_id, {})
        start = sec.get("start_page")
        end = sec.get("end_page")
        if start is not None and end is not None:
            ranges.append((int(start), int(end)))
    return ranges, "COVERED_IN section ranges (fallback)"


# ── Qdrant helpers ─────────────────────────────────────────────────────────────

def get_client():
    """Return a QdrantClient — path mode if QDRANT_PATH is set, else server mode."""
    from qdrant_client import QdrantClient

    path = os.environ.get("QDRANT_PATH", "")
    if path:
        print(f"[qdrant] Using on-disk storage at: {path}")
        return QdrantClient(path=path)

    host = os.environ.get("QDRANT_HOST", "localhost")
    port = int(os.environ.get("QDRANT_PORT", "6333"))
    print(f"[qdrant] Connecting to server at {host}:{port}")
    return QdrantClient(host=host, port=port)


def embed_query(query: str) -> list[float]:
    """Embed the query via OpenRouter; fall back to OpenAI direct."""
    from openai import OpenAI

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        try:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            resp = client.embeddings.create(model=EMBED_MODEL, input=[query])
            return resp.data[0].embedding
        except Exception as exc:
            print(f"  OpenRouter failed ({exc}), trying OpenAI direct...")

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        print("ERROR: Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set.")
        sys.exit(1)
    client = OpenAI(base_url="https://api.openai.com/v1", api_key=openai_key)
    resp = client.embeddings.create(model="text-embedding-3-small", input=[query])
    return resp.data[0].embedding


# ── LLM synthesis ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a teaching assistant for the textbook "Elements of Causal Inference" \
(Peters, Janzing, Schölkopf, 2017).
Answer the user's question using ONLY the passages provided below.
If the passages do not contain enough information to answer, say so explicitly — \
do NOT add knowledge from outside the provided text.
Cite the source of each claim as (ch<N>, p<M>)."""


def synthesize(query: str, passages: list) -> None:
    """Call the LLM with retrieved passages as context and stream the answer."""
    from openai import OpenAI

    if not passages:
        return

    # Build context block from retrieved passages
    context_parts = []
    for r in passages:
        p = r.payload
        header = f"[ch{p['chapter']}, p{p['page_num']}]"
        context_parts.append(f"{header}\n{p['content']}")
    context = "\n\n---\n\n".join(context_parts)

    user_msg = f"Passages:\n\n{context}\n\nQuestion: {query}"

    api_key = os.environ.get("OPENROUTER_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("WARN: No API key found — skipping synthesis.")
        return

    base_url = (
        "https://openrouter.ai/api/v1"
        if os.environ.get("OPENROUTER_API_KEY")
        else "https://api.openai.com/v1"
    )
    model = SYNTH_MODEL if os.environ.get("OPENROUTER_API_KEY") else "gpt-5-mini"

    client = OpenAI(base_url=base_url, api_key=api_key)

    print(f"\n{'='*70}")
    print(f"[synthesis]  model={model}")
    print(f"{'='*70}\n")

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print(f"\n\n{'='*70}")


# ── Search ─────────────────────────────────────────────────────────────────────

def search(query: str, top_k: int = 5, concept_id: str | None = None, no_synth: bool = False) -> None:
    from qdrant_client.models import FieldCondition, Filter, Range

    qdrant = get_client()

    if not qdrant.collection_exists(COLLECTION):
        print(f"ERROR: Collection '{COLLECTION}' not found. Run the ingester first.")
        sys.exit(1)

    info = qdrant.get_collection(COLLECTION)
    print(f"[qdrant] Collection '{COLLECTION}': {info.points_count} points")

    # ── Build graph-anchored filter ──────────────────────────────────────────
    q_filter = None
    if concept_id:
        nodes_by_id, edges = load_graph()
        concept_id = slugify(concept_id)  # "common cause" → "common_cause"

        if concept_id not in nodes_by_id:
            print(f"ERROR: concept '{concept_id}' not found in graph.")
            print("  Hint: use the slugified id, e.g. 'backdoor_criterion'")
            sys.exit(1)

        page_ranges, strategy = get_page_ranges(concept_id, nodes_by_id, edges)

        if page_ranges:
            print(f"[graph]  concept '{concept_id}' → {strategy}")
            print(f"         {len(page_ranges)} range(s): {page_ranges}")
            q_filter = Filter(
                should=[
                    FieldCondition(key="page_num", range=Range(gte=s, lte=e))
                    for s, e in page_ranges
                ]
            )
        else:
            print(f"[graph]  concept '{concept_id}' has no page refs or COVERED_IN edges — global fallback")

    print(f"\nEmbedding query: {query!r}")
    vec = embed_query(query)

    response = qdrant.query_points(
        collection_name=COLLECTION,
        query=vec,
        query_filter=q_filter,
        limit=top_k,
    )
    results = response.points

    if not results:
        print("No results found.")
        return

    print(f"\n{'='*70}")
    for i, r in enumerate(results, 1):
        p = r.payload
        heading = p.get("section_heading") or "(none)"
        print(f"\n[{i}] score={r.score:.4f}  ch={p['chapter']}  page={p['page_num']}")
        print(f"    section: {heading}")
        snippet = p["content"][:500].replace("\n", " ")
        print(f"    content: {snippet}...")
    print(f"\n{'='*70}")

    if not no_synth:
        synthesize(query, results)


_EPILOG = """
modes
-----
  Pure vector search (no graph):
    Embeds QUERY and runs cosine similarity across all 238 ingested pages.
    Use when you want broad coverage or are exploring without a specific concept.

  GraphRAG search (--concept):
    1. Looks up CONCEPT_ID in src/graph/output/eci_graph.json
    2. Uses page_refs (exact index pages ± 1) when available — most precise.
       Falls back to COVERED_IN section ranges if page_refs is absent.
    3. Restricts Qdrant search to those pages only, then ranks by vector score.
    4. Retrieved passages are fed to an LLM (openai/gpt-4o-mini via OpenRouter)
       which summarises the answer. The LLM is instructed to cite passages and
       never hallucinate beyond what the text provides.
    Use --no-synth to skip step 4 and see raw passages only.

concept ids
-----------
  IDs are slugified: lowercase, spaces/hyphens → underscores.
  "common cause"       → common_cause
  "backdoor criterion" → backdoor_criterion
  "D-separation"       → d_separation
  Natural names are accepted too — the script normalises them automatically.

environment variables
---------------------
  QDRANT_HOST        Qdrant server hostname        (default: localhost)
  QDRANT_PORT        Qdrant server port            (default: 6333)
  QDRANT_PATH        On-disk storage path          (overrides host/port — no server needed)
  OPENROUTER_API_KEY API key for query embedding   (loaded from .env automatically)
  OPENAI_API_KEY     Fallback if OpenRouter fails

examples
--------
  # Pure vector search
  python scripts/qdrant_search.py "what is a structural causal model" --top-k 5

  # Graph-anchored — exact index pages for the concept
  python scripts/qdrant_search.py "backdoor criterion definition" --concept backdoor_criterion

  # Spaces in concept name are fine
  python scripts/qdrant_search.py "what causes confounding" --concept "common cause" --top-k 3

  # Use on-disk storage (no server required)
  QDRANT_PATH=/data/users/yyx/onProject/CHAI/EducAgent/qdrant_storage \\
    python scripts/qdrant_search.py "d-separation rules" --concept d_separation
"""

def main() -> None:
    parser = argparse.ArgumentParser(
        description="GraphRAG search over ECI (Elements of Causal Inference) passages.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Natural-language query string")
    parser.add_argument(
        "--concept",
        default=None,
        metavar="CONCEPT_ID",
        help=(
            "Graph-anchor concept name or id (e.g. 'backdoor_criterion' or "
            "'backdoor criterion'). Restricts search to that concept's index pages "
            "(precise) or COVERED_IN section ranges (fallback)."
        ),
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument("--no-synth", action="store_true", help="Skip LLM synthesis, show retrieved passages only")
    args = parser.parse_args()

    search(args.query, top_k=args.top_k, concept_id=args.concept, no_synth=args.no_synth)


if __name__ == "__main__":
    main()
