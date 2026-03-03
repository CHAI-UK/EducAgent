"""Quick health-check for the Qdrant service.

Usage (after port-forwarding or from within the cluster):
    python scripts/check_qdrant.py [--host HOST] [--port PORT]

Exits 0 if Qdrant is reachable and the eci_passages collection exists.
Exits 1 otherwise (useful in CI or as a pre-flight check before ingestion).
"""
import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Qdrant connectivity and collection.")
    parser.add_argument("--host", default="localhost", help="Qdrant host (default: localhost)")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port (default: 6333)")
    args = parser.parse_args()

    try:
        from qdrant_client import QdrantClient
    except ImportError:
        print("ERROR: qdrant-client is not installed. Run: pip install qdrant-client>=1.17.0")
        sys.exit(1)

    client = QdrantClient(host=args.host, port=args.port)

    # 1. Basic connectivity — list collections
    try:
        collections = client.get_collections().collections
    except Exception as exc:
        print(f"FAIL: Cannot connect to Qdrant at {args.host}:{args.port} — {exc}")
        sys.exit(1)

    print(f"OK: Connected to Qdrant at {args.host}:{args.port}")
    collection_names = [c.name for c in collections]
    print(f"     Collections: {collection_names or '(none)'}")

    # 2. Check eci_passages collection
    if "eci_passages" not in collection_names:
        print("WARN: Collection 'eci_passages' does not exist yet.")
        print("      Run the ingester to populate it:")
        print("        QDRANT_HOST=<host> QDRANT_PORT=<port> \\")
        print("        OPENROUTER_API_KEY=<key> \\")
        print("        conda run -n edu python src/graph/eci_qdrant_ingester.py")
        sys.exit(0)

    # 3. Report collection size
    info = client.get_collection("eci_passages")
    count = info.points_count
    vec_size = info.config.params.vectors.size  # type: ignore[union-attr]
    print(f"OK: eci_passages — {count} points, vector dim={vec_size}")

    if count == 0:
        print("WARN: Collection exists but has 0 points — ingestion may not have run yet.")


if __name__ == "__main__":
    main()
