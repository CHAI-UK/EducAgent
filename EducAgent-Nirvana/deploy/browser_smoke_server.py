"""Maintainer-only Chrome fixture: real Portal runtime, offline TestModel."""

import argparse
from pathlib import Path
import sys

import build_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4186)
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(build_bundle.WORKSPACE / "EducAgent-SDK"))
    from examples.playable_demo import _build_module, _load_registry
    from educagent_sdk.course_introductions import load_course_introductions
    from educagent_sdk.web_demo import create_browser_session_server
    from pydantic_ai.models.test import TestModel

    bundle = args.data_dir / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    build_bundle.stage_bundle(bundle)
    sdk = build_bundle.WORKSPACE / "EducAgent-SDK"
    entries = _load_registry(sdk / "content/modules.json")
    introductions = load_course_introductions(sdk / "content/course_introductions.json")

    def modules(directory):
        return [_build_module(entry, events_root=directory, reset=False,
                              introduction_catalog=introductions) for entry in entries]

    server = create_browser_session_server(
        modules, sessions_root=args.data_dir / "browser-sessions", model_factory=TestModel,
        port=args.port, static_root=bundle / "site",
    )
    print(f"Offline Chrome fixture on http://127.0.0.1:{args.port}/portal/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
