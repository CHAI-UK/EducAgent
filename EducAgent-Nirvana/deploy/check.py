"""Verify bundle integrity and HTTP routing without sending a model request."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent


def verify_bundle(root: Path) -> int:
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if root.resolve() not in path.parents:
            raise ValueError("manifest contains an unsafe path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"bundle integrity check failed: {name}")
    return len(manifest["files"])


def check_http(base: str, *, liveness_only: bool = False) -> None:
    routes = [("/healthz", 200), ("/api/health", 200), ("/nirvana/api/health", 200)] if liveness_only else [
                            ("/", 200), ("/portal/", 200), ("/nirvana/", 200),
                            ("/healthz", 200), ("/api/health", 200), ("/api/modules", 200),
                            ("/nirvana/api/health", 200), ("/styles.css", 200),
                            ("/nirvana/config.js", 200), ("/nirvana/app.js", 200), ("/.env", 404),
                            ("/authoring/content-pack-editor.html", 404),
                            ("/api/validate-content-pack", 404), ("/api/preview", 404)]
    for route, expected in routes:
        try:
            with urlopen(base.rstrip("/") + route, timeout=5) as response:
                status = response.status
                body = response.read()
        except HTTPError as error:
            status, body = error.code, error.read()
        if status != expected:
            raise ValueError(f"{route}: expected HTTP {expected}, got {status}")
        if route == "/api/modules" and len(json.loads(body)["modules"]) != 3:
            raise ValueError("expected three Portal modules")
        if route == "/api/health" and json.loads(body).get("progress_scope") != "browser_session":
            raise ValueError("Portal does not have browser-session isolation enabled")
        if route == "/nirvana/api/health" and json.loads(body).get("status") != "ready":
            raise ValueError("Nirvana is not ready")
        if route == "/nirvana/config.js" and b'"/nirvana/api"' not in body:
            raise ValueError("Nirvana is not configured for the same-origin API")
        if route == "/portal/":
            script = re.search(rb'<script[^>]+src="([^"]+)"', body)
            if script is None:
                raise ValueError("Portal entry script is missing")
            asset = urljoin("/portal/", script[1].decode("utf-8"))
            if not asset.startswith("/portal/assets/"):
                raise ValueError("Portal entry script must be a bundled local asset")
            routes.append((asset, 200))
        print(f"PASS {route}: HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:9090")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--liveness-only", action="store_true", help="Skip the single-user Portal API while a Tutor turn may be running.")
    args = parser.parse_args()
    try:
        print(f"Bundle integrity: {verify_bundle(ROOT)} files verified.")
        if not args.verify_only:
            check_http(args.url, liveness_only=args.liveness_only)
        print("No ELM request was made. HTTP readiness does not verify ELM credentials or model availability.")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
