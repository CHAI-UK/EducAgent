"""LAN binding and exact-origin CORS checks without provider requests."""

import threading
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
import unittest
from http.client import HTTPConnection
from unittest.mock import patch

from demo_server import create_server


class LanTest(unittest.TestCase):
    def test_post_origin_and_json_checks_run_before_any_operation(self):
        from http.server import HTTPServer

        original = HTTPServer.server_bind
        calls = []

        def ephemeral(server):
            server.server_address = ("127.0.0.1", 0)
            original(server)

        async def operation(payload, *, model):
            calls.append(payload)
            return {"task": "effect", "reply": "Offline response"}

        with patch.object(HTTPServer, "server_bind", ephemeral), \
                patch("demo_server.run_frame", operation), \
                patch("demo_server.run_classify", operation), \
                patch("demo_server.run_chat", operation):
            server = create_server(model="unused", origin_port=4173, lan_address="10.126.222.170")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def post(path, headers):
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                try:
                    connection.request("POST", path, body='{"message":"fictional probe"}', headers=headers)
                    response = connection.getresponse()
                    status = response.status
                    response.read()
                    return status
                finally:
                    connection.close()

            try:
                for path in ("/api/frame", "/api/classify", "/api/chat"):
                    for origin in ("https://untrusted.example", "null", "https://learn.chai.ac.uk/not-an-origin"):
                        with self.subTest(path=path, origin=origin):
                            self.assertEqual(post(path, {"Origin": origin, "Content-Type": "application/json"}), 403)
                            self.assertEqual(calls, [])
                    for content_type in (None, "text/plain", "application/x-www-form-urlencoded"):
                        headers = {} if content_type is None else {"Content-Type": content_type}
                        with self.subTest(path=path, content_type=content_type):
                            self.assertEqual(post(path, headers), 415)
                            self.assertEqual(calls, [])
                # Retain CLI, local, explicitly opted-in LAN, and public TLS
                # origins when the reverse proxy preserves the public Host.
                accepted = (
                    {},
                    {"Origin": "http://127.0.0.1:4173"},
                    {"Origin": "http://localhost:4173"},
                    {"Origin": "http://10.126.222.170:4173"},
                    {"Origin": "https://learn.chai.ac.uk", "Host": "learn.chai.ac.uk"},
                    {"Origin": "https://learn.chai.ac.uk:9443", "Host": "learn.chai.ac.uk:9443"},
                )
                for headers in accepted:
                    with self.subTest(accepted=headers):
                        self.assertEqual(post("/api/frame", {"Content-Type": "application/json; charset=utf-8", **headers}), 200)
                self.assertEqual(len(calls), len(accepted))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_background_frame_does_not_block_classification(self):
        from http.server import HTTPServer
        original = HTTPServer.server_bind
        def ephemeral(server):
            server.server_address = ("127.0.0.1", 0)
            original(server)
        started, release = threading.Event(), threading.Event()
        async def slow_frame(payload, *, model):
            started.set()
            while not release.is_set():
                await asyncio.sleep(0.01)
            return {"task": "effect", "fields": {}, "reply": "ready"}
        async def quick_classify(payload, *, model):
            return {"task": "shift", "reason": "New question"}
        with patch.object(HTTPServer, "server_bind", ephemeral), patch("demo_server.run_frame", slow_frame), patch("demo_server.run_classify", quick_classify):
            server = create_server(model="unused")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def post(path):
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                try:
                    connection.request("POST", path, body='{"message":"fictional"}', headers={"Content-Type":"application/json"})
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    return json.loads(response.read())
                finally:
                    connection.close()
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    pending = pool.submit(post, "/api/frame")
                    try:
                        self.assertTrue(started.wait(3))
                        self.assertEqual(post("/api/classify")["task"], "shift")
                        self.assertFalse(pending.done())
                    finally:
                        release.set()
                    self.assertEqual(pending.result(timeout=3)["task"], "effect")
            finally:
                release.set()
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_explicit_lan_origin_and_default_loopback(self):
        # Bind an ephemeral port while preserving production port validation.
        from http.server import HTTPServer

        original = HTTPServer.server_bind

        def ephemeral(server):
            server.server_address = (server.server_address[0], 0)
            original(server)

        for address in (None, "10.126.222.170"):
            with patch.object(HTTPServer, "server_bind", ephemeral):
                server = create_server(model="unused", lan_address=address, origin_port=4173)
            self.assertEqual(server.server_address[0], "0.0.0.0" if address else "127.0.0.1")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for origin in ("http://127.0.0.1:4173", "http://10.126.222.170:4173", "http://untrusted.example:4173"):
                    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    connection.request("OPTIONS", "/api/frame", headers={"Origin": origin})
                    response = connection.getresponse()
                    allowed = origin == "http://127.0.0.1:4173" or (address and origin == f"http://{address}:4173")
                    self.assertEqual(response.getheader("Access-Control-Allow-Origin"), origin if allowed else None)
                    response.read()
                    connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
