"""Maintainer Linux proxy check with disposable mock APIs, never ELM/user state.

This checks the real Nginx binary, same-origin routing and static boundary.
It does not replace running the actual deployment image on the target server.
"""

import argparse
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
import time
from urllib.request import urlopen

import build_bundle
import check
import run


class FixtureAPI(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        payload = {"modules": [{"module_id": name} for name in ("causality_m0", "m1_effect", "m1_shift")]} \
            if self.path == "/api/modules" else {"status": "ready"}
        if self.path == "/api/health" and self.server.server_port == 9091:
            payload = {"status": "ok", "progress_scope": "browser_session"}
        encoded = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):  # noqa: N802
        if self.headers.get("Origin") != "http://" + self.headers.get("Host", ""):
            self.send_error(403, "Origin/Host mismatch")
            return
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        encoded = json.dumps({"fixture": True, "path": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nginx", required=True)
    parser.add_argument("--mime-types", default="/etc/nginx/mime.types")
    args = parser.parse_args()
    servers = []
    children = []
    try:
        with ExitStack() as cleanup:
            temporary = cleanup.enter_context(tempfile.TemporaryDirectory(prefix="educagent-proxy-check-"))
            cleanup.callback(run.stop_children, children)
            root = Path(temporary)
            bundle = root / "bundle"
            bundle.mkdir()
            build_bundle.stage_bundle(bundle)
            text = run.render_nginx((bundle / "nginx.conf.template").read_text(), site=bundle / "site",
                                    runtime=root, bind="127.0.0.1")
            text = text.replace("/etc/nginx/mime.types", Path(args.mime_types).resolve().as_posix())
            config = root / "nginx.conf"
            config.write_text(text)
            subprocess.run([args.nginx, "-t", "-e", "stderr", "-p", str(root) + "/", "-c", str(config)], check=True)
            for port in (9091, 9092):
                server = ThreadingHTTPServer(("127.0.0.1", port), FixtureAPI)
                servers.append(server)
                Thread(target=server.serve_forever, daemon=True).start()
            children.append(subprocess.Popen([args.nginx, "-e", "stderr", "-p", str(root) + "/", "-c", str(config), "-g", "daemon off;"]))
            deadline = time.monotonic() + 5
            while True:
                try:
                    with urlopen("http://127.0.0.1:9090/healthz", timeout=1):
                        break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.1)
            check.check_http("http://127.0.0.1:9090")
            from urllib.request import Request
            for path, upstream in (("/api/select-profile", "/api/select-profile"),
                                   ("/nirvana/api/classify", "/api/classify"),
                                   ("/nirvana/api/frame", "/api/frame")):
                with urlopen(Request("http://127.0.0.1:9090" + path, data=b"{}",
                                     headers={"Content-Type": "application/json",
                                              "Origin": "http://127.0.0.1:9090"})) as response:
                    assert json.load(response)["path"] == upstream
                print(f"PASS POST rewrite {path} -> {upstream}")
            print("Real Nginx routing/static check passed against disposable mock APIs. No ELM request.")
            run.stop_children(children)
            children.clear()
    finally:
        run.stop_children(children)
        for server in servers:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
