"""Local HTTP boundary for the guarded demo and its optional Astryx client."""

import asyncio
import json
import mimetypes
import re
import secrets
import sys
import traceback
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from http.cookies import CookieError, SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from typing import Any
from urllib.parse import unquote, urlparse
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError
from pydantic_ai.models import Model

from .causal_scene import CausalSceneAction
from .experiments import ExperimentAction
from .demo import DemoController
from .diagnostic import DiagnosticSession
from .contracts import ContentPack
from .course_introductions import CourseIntroductionView
from .release import ReleaseValidationError, validate_release


def _validate_content_pack(value: Any) -> dict[str, Any]:
    try:
        pack = ContentPack.model_validate_json(json.dumps(value))
    except ValidationError as exc:
        return {"valid": False, "releasable": False, "issues": [
            {"path": "/" + "/".join(map(str, item["loc"])), "message": item["msg"]}
            for item in exc.errors(include_input=False, include_url=False)
        ], "unused_resource_ids": []}
    try:
        report = validate_release(pack)
    except ReleaseValidationError as exc:
        report = exc.report
    return {"valid": True, "releasable": report.releasable,
            "issues": [item.model_dump() for item in report.issues],
            "unused_resource_ids": list(report.unused_resource_ids)}


def _authoring_page(client_address: str) -> str | None:
    if client_address != "127.0.0.1":
        return None
    path = Path(__file__).resolve().parents[2] / "web/tools/content-pack-editor.html"
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _request_failure(exc: Exception, request_id: str) -> tuple[HTTPStatus, dict[str, Any]]:
    """Classify command errors separately from provider/configuration failures."""
    if isinstance(exc, (TypeError, ValueError, KeyError)):
        detail = str(exc)[:500]
        state_error = any(word in detail.lower() for word in (
            "awaiting", "pending", "locked", "not active", "not started",
            "completed", "before starting", "cannot continue", "cannot advance", "not ready",
            "stale revision", "experiment is frozen", "current open attempt",
        ))
        return (HTTPStatus.CONFLICT if state_error else HTTPStatus.BAD_REQUEST), {
            "error": "learning state conflict" if state_error else "invalid request",
            "code": "invalid_state" if state_error else "invalid_request",
            "detail": detail,
            "request_id": request_id,
            "retryable": False,
            "recovery": "Refresh the learning state and retry the available action." if state_error
            else "Check the requested action and input.",
        }
    upstream_status = getattr(exc, "status_code", None)
    if type(upstream_status) is not int or not 100 <= upstream_status <= 599:
        upstream_status = None
    configuration_error = type(exc).__name__ == "UserError" or upstream_status in {401, 403, 404}
    timed_out = isinstance(exc, TimeoutError) or type(exc).__name__ in {"APITimeoutError", "ReadTimeout", "ConnectTimeout"}
    failure = {
        "error": "tutor configuration error" if configuration_error else "tutor unavailable",
        "code": "tutor_configuration" if configuration_error else "tutor_unavailable",
        "diagnostic": type(exc).__name__,
        "request_id": request_id,
        "retryable": not configuration_error,
        "recovery": "Ask the local server owner to check its model configuration." if configuration_error
        else "The tutor took too long. Your learning record is preserved; retry the saved request." if timed_out
        else "Your learning record is preserved. Retry the saved request when the tutor is available.",
    }
    if upstream_status is not None:
        failure["upstream_status"] = upstream_status
    return HTTPStatus.SERVICE_UNAVAILABLE, failure


def _practical_mission(controller: DemoController) -> dict[str, str] | None:
    activity = next((item for item in controller.pack.activities if item.causal_scene_id is not None), None)
    if activity is None:
        return None
    scene = next(item for item in controller.pack.causal_scenes if item.scene_id == activity.causal_scene_id)
    return {"activity_id": activity.activity_id, "title": scene.title}


def _is_public_asset(path: Path) -> bool:
    """Allow built web assets, never authoring material or development state."""
    if any(part.startswith(".") or ":" in part for part in path.parts):
        return False
    if len(path.parts) == 1:
        return path.name in {"index.html", "styles.css", "sources.html", "favicon.ico"}
    return path.parts[0] in {"assets", "media", "portal", "nirvana"} and path.suffix.lower() in {
        ".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg",
        ".ico", ".woff", ".woff2", ".ttf", ".avif",
    }


def create_demo_server(
    controller: DemoController,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    model: Model | str,
    diagnostic: DiagnosticSession | None = None,
    static_root: str | Path | None = None,
    unguarded_tutor: bool = False,
    allow_lan: bool = False,
) -> HTTPServer:
    """Create a single-user demo server; LAN binding requires explicit opt-in."""

    if host != "127.0.0.1" and not (allow_lan and host == "0.0.0.0"):
        raise ValueError("the local demo server may bind only to 127.0.0.1")
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    if model is None:
        raise ValueError("the local demo server requires a guarded tutor model")
    runner = asyncio.Runner()
    root = None if static_root is None else Path(static_root).resolve()
    if root is not None and not root.is_dir():
        raise ValueError("static_root must be an existing directory")

    class DemoHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - required stdlib handler name
            path = urlparse(self.path).path
            if path == "/authoring/content-pack-editor.html" and host == "127.0.0.1":
                page = _authoring_page(self.client_address[0])
                if page is not None:
                    self._html(page)
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            elif path == "/api/state":
                self._json(HTTPStatus.OK, _state(controller, diagnostic, model))
            elif path == "/api/trace":
                self._json(HTTPStatus.OK, controller.developer_trace())
            else:
                self._static(path)

        def do_POST(self) -> None:  # noqa: N802 - required stdlib handler name
            path = urlparse(self.path).path
            body: dict[str, Any] = {}
            request_id = f"http.{uuid4().hex}"
            try:
                body = self._body()
                request_id = body.get("request_id") or request_id
                if path == "/api/validate-content-pack":
                    self._json(HTTPStatus.OK, _validate_content_pack(body["pack"]))
                    return
                result = runner.run(
                    _handle_command(
                        controller,
                        path,
                        body,
                        model=model,
                        diagnostic=diagnostic,
                        unguarded_tutor=unguarded_tutor,
                    )
                )
                self._json(HTTPStatus.OK, result)
            except Exception as exc:
                # Exception messages from providers may contain payloads or secrets.
                status, failure = _request_failure(exc, str(request_id))
                upstream = failure.get("upstream_status")
                detail = "" if upstream is None else f"; upstream HTTP {upstream}"
                print(f"Request {request_id} to {path} failed ({type(exc).__name__}{detail}).",
                      file=sys.stderr, flush=True)
                self._json(status, failure)

        def _body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            maximum = 524_288 if urlparse(self.path).path == "/api/validate-content-pack" else 8_192
            if length < 0 or length > maximum:
                raise ValueError("request body is too large")
            value = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(value, dict):
                raise ValueError("request body must be an object")
            return value

        def _static(self, path: str) -> None:
            if root is None:
                if path == "/":
                    self._html(_FALLBACK_PAGE)
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            decoded = unquote(path)
            if "\\" in decoded or "\x00" in decoded or ".." in decoded.split("/"):
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            relative_path = "index.html" if path == "/" else decoded.lstrip("/")
            candidate = (root / relative_path).resolve()
            if root not in candidate.parents and candidate != root:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            if candidate.is_dir():
                candidate = (candidate / "index.html").resolve()
                if root not in candidate.parents:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
            # Check both the request and resolved target, including symlinks.
            requested = Path(relative_path)
            if requested.suffix == "":
                requested /= "index.html"
            if (
                not _is_public_asset(requested)
                or not _is_public_asset(candidate.relative_to(root))
                or not candidate.is_file()
            ):
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            if decoded != "/" and not decoded.endswith("/") and Path(relative_path).suffix == "":
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                self.send_header("Location", path + "/")
                self.end_headers()
                return
            body = candidate.read_bytes()
            content_type = mimetypes.guess_type(candidate.name)[0]
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type", content_type or "application/octet-stream"
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, value: str) -> None:
            body = value.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
            body = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            """Keep local learner actions out of terminal logs by default."""

    class DemoServer(HTTPServer):
        def server_close(self) -> None:
            runner.close()
            super().server_close()

    return DemoServer((host, port), DemoHandler)


@dataclass(frozen=True)
class ProfileRuntime:
    """One normal course audience with fixed scoring, teaching and diagnostic state."""

    controller: DemoController
    diagnostic: DiagnosticSession | None = None


@dataclass(frozen=True)
class ModuleRuntime:
    """One learner-selectable module wired to its own controller and progress."""

    module_id: str
    title: str
    optional: bool
    prerequisite_module_ids: tuple[str, ...]
    nirvana_task: str | None
    controller: DemoController
    diagnostic: DiagnosticSession | None = None
    lesson_samples: dict[str, DemoController] = field(default_factory=dict)
    profiles: dict[str, ProfileRuntime] = field(default_factory=dict)
    introductions: dict[str, CourseIntroductionView] | None = None


class _HubTransport(BaseHTTPRequestHandler):
    """Shared HTTP transport for a single hub and cookie-routed hubs."""

    _static_root: Path | None = None
    _browser_cookie: str | None = None

    def end_headers(self) -> None:
        if self._browser_cookie is not None:
            self.send_header("Set-Cookie", self._browser_cookie)
        super().end_headers()

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        maximum = 524_288 if urlparse(self.path).path == "/api/validate-content-pack" else 8_192
        if length < 0 or length > maximum:
            raise ValueError("request body is too large")
        value = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(value, dict):
            raise ValueError("request body must be an object")
        return value

    def _static(self, path: str) -> None:
        root = self._static_root
        if root is None:
            if path == "/":
                self._html(_FALLBACK_PAGE)
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        decoded = unquote(path)
        if "\\" in decoded or "\x00" in decoded or ".." in decoded.split("/"):
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        relative_path = "index.html" if path == "/" else decoded.lstrip("/")
        candidate = (root / relative_path).resolve()
        if root not in candidate.parents and candidate != root:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if candidate.is_dir():
            candidate = (candidate / "index.html").resolve()
            if root not in candidate.parents:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
        requested = Path(relative_path)
        if requested.suffix == "":
            requested /= "index.html"
        if (not _is_public_asset(requested)
                or not _is_public_asset(candidate.relative_to(root)) or not candidate.is_file()):
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if decoded != "/" and not decoded.endswith("/") and Path(relative_path).suffix == "":
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header("Location", path + "/")
            self.end_headers()
            return
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, value: str) -> None:
        body = value.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        """Keep learner actions and bearer cookies out of terminal logs."""


def create_module_hub_server(
    modules: list[ModuleRuntime],
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    model: Model | str,
    static_root: str | Path | None = None,
    unguarded_tutor: bool = False,
    allow_lan: bool = False,
    open_modules: bool = True,
) -> HTTPServer:
    """Create a single-user demo server that can switch between several modules.

    This wraps the single-module ``/api/*`` command handling in ``_handle_command``
    and ``_state`` unchanged; it only adds the module registry, lock status, and
    the currently active module on top of that existing, tested behaviour.
    """

    handler, close = _create_module_hub_application(
        modules, host=host, port=port, model=model, static_root=static_root,
        unguarded_tutor=unguarded_tutor, allow_lan=allow_lan, open_modules=open_modules,
    )

    class HubServer(HTTPServer):
        def server_close(self) -> None:
            close()
            super().server_close()

    try:
        return HubServer((host, port), handler)
    except Exception:
        close()
        raise


def create_browser_session_server(
    module_factory: Callable[[Path], list[ModuleRuntime]], *,
    sessions_root: str | Path, model_factory: Callable[[], Model | str],
    host: str = "127.0.0.1", port: int = 8000,
    static_root: str | Path | None = None, unguarded_tutor: bool = False,
    allow_lan: bool = False, open_modules: bool = True,
    secure_cookie: bool = False, max_cached_sessions: int = 32,
) -> HTTPServer:
    """Serve independent anonymous browser sessions on one listening socket.

    The factory receives a validated private session directory, never cookie
    text. It must build fresh controllers/stores there and must not copy legacy
    shared progress. Each cached session owns its model, event loop and lock.
    Idle eviction closes these resources, not persisted learning records.
    Cookies are session-only bearer credentials; they are not user accounts.
    """

    if host != "127.0.0.1" and not (allow_lan and host == "0.0.0.0"):
        raise ValueError("the local demo server may bind only to 127.0.0.1")
    if not 0 <= port <= 65535 or type(max_cached_sessions) is not int or max_cached_sessions < 1:
        raise ValueError("invalid port or session cache capacity")
    directory = Path(sessions_root).resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    root = None if static_root is None else Path(static_root).resolve()
    if root is not None and not root.is_dir():
        raise ValueError("static_root must be an existing directory")
    cookie_name = "educagent_portal_session"
    cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
    cache_lock = RLock()

    def _session_directory(token: str) -> Path | None:
        if re.fullmatch(r"[0-9a-f]{64}", token) is None:
            return None
        candidate = directory / token
        if candidate.is_symlink() or not candidate.is_dir() or candidate.resolve().parent != directory:
            return None
        marker = candidate / ".browser-session"
        return candidate if marker.is_file() and not marker.is_symlink() else None

    def _acquire(cookie_header: str) -> tuple[dict[str, Any], str | None]:
        cookies: SimpleCookie = SimpleCookie()
        try:
            cookies.load(cookie_header)
        except CookieError:
            pass
        token = cookies[cookie_name].value if cookie_name in cookies else ""
        with cache_lock:
            session_dir = _session_directory(token)
            set_cookie = None
            if (session_dir is None or token not in cache) and len(cache) >= max_cached_sessions:
                idle = next((key for key, value in cache.items() if value["users"] == 0), None)
                if idle is None:
                    raise RuntimeError("browser session capacity is busy; retry shortly")
                cache.pop(idle)["close"]()
            if session_dir is None:
                token = secrets.token_hex(32)
                session_dir = directory / token
                session_dir.mkdir(mode=0o700)
                (session_dir / ".browser-session").touch(mode=0o600)
                set_cookie = f"{cookie_name}={token}; Path=/; HttpOnly; SameSite=Lax"
                if secure_cookie:
                    set_cookie += "; Secure"
            if token not in cache:
                model = model_factory()
                try:
                    handler, close = _create_module_hub_application(
                        module_factory(session_dir), host=host, port=port, model=model,
                        static_root=root, unguarded_tutor=unguarded_tutor, allow_lan=allow_lan,
                        open_modules=open_modules, selection_path=session_dir / "selection.json",
                        close_model=True,
                    )
                except Exception:
                    client = getattr(model, "client", None)
                    if client is not None and hasattr(client, "close"):
                        with asyncio.Runner() as cleanup:
                            cleanup.run(client.close())
                    raise
                cache[token] = {"handler": handler, "close": close, "lock": RLock(), "users": 0}
            cache.move_to_end(token)
            application = cache[token]
            application["users"] += 1
            return application, set_cookie

    class BrowserHandler(_HubTransport):
        _static_root = root

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/health":
                self._json(HTTPStatus.OK, {"status": "ok", "progress_scope": "browser_session"})
            elif path == "/authoring/content-pack-editor.html" and host == "127.0.0.1":
                page = _authoring_page(self.client_address[0])
                if page is None:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                else:
                    self._html(page)
            elif path.startswith("/api/"):
                self._dispatch("do_GET")
            else:
                self._static(path)

        def do_POST(self) -> None:  # noqa: N802
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                # Consume an ordinary bounded body before closing the socket;
                # otherwise Windows may reset it before the 403 is delivered.
                try:
                    self._body()
                except ValueError:
                    pass
                self._json(HTTPStatus.FORBIDDEN, {"error": "cross-origin commands are not allowed"})
                return
            self._dispatch("do_POST")

        def _dispatch(self, method: str) -> None:
            application = None
            try:
                application, self._browser_cookie = _acquire(self.headers.get("Cookie", ""))
                with application["lock"]:
                    getattr(application["handler"], method)(self)
            except Exception as exc:
                # A cookie is a bearer secret: never include it, paths or raw
                # exception messages in logs or error responses.
                print(f"Browser session request failed ({type(exc).__name__}).", file=sys.stderr, flush=True)
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {
                    "error": "browser session unavailable", "code": "session_unavailable",
                    "retryable": True, "recovery": "Retry shortly; saved progress is preserved.",
                })
            finally:
                if application is not None:
                    with cache_lock:
                        application["users"] -= 1

    class BrowserSessionServer(ThreadingHTTPServer):
        daemon_threads = False
        block_on_close = True

        def server_close(self) -> None:
            super().server_close()
            with cache_lock:
                for application in cache.values():
                    application["close"]()
                cache.clear()

    return BrowserSessionServer((host, port), BrowserHandler)


def _create_module_hub_application(
    modules: list[ModuleRuntime], *, host: str, port: int, model: Model | str,
    static_root: str | Path | None, unguarded_tutor: bool, allow_lan: bool,
    open_modules: bool, selection_path: Path | None = None, close_model: bool = False,
) -> tuple[type[BaseHTTPRequestHandler], Callable[[], None]]:
    """Build isolated hub state without binding a listening socket."""

    if not modules:
        raise ValueError("at least one module is required")
    if len({module.module_id for module in modules}) != len(modules):
        raise ValueError("module_id values must be unique")
    for module in modules:
        if module.introductions is not None:
            if module.module_id not in {"m1_effect", "m1_shift"}:
                raise ValueError("course introductions belong only to the authored M1 modules")
            if set(module.introductions) != set(module.profiles):
                raise ValueError("course introductions must match the module profiles")
            if any(view.profile_id != profile_id or view.title != module.title
                   for profile_id, view in module.introductions.items()):
                raise ValueError("course introductions must match their profile and module title")
            for view in module.introductions.values():
                other = next((item for item in modules if item.module_id == view.comparison.other_module_id), None)
                if other is None or other.title != view.comparison.other_title:
                    raise ValueError("course comparison must reference another registered course")
        for profile_id, runtime in module.profiles.items():
            if profile_id not in {"general", "medical"} or runtime.controller.profile_id != profile_id:
                raise ValueError("course profiles must match their fixed controller audience")
            if runtime.diagnostic is not None and runtime.diagnostic.pack != runtime.controller.pack:
                raise ValueError("profile diagnostic must use its controller's scored pack")
    if host != "127.0.0.1" and not (allow_lan and host == "0.0.0.0"):
        raise ValueError("the local demo server may bind only to 127.0.0.1")
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    if model is None:
        raise ValueError("the local demo server requires a guarded tutor model")
    root = None if static_root is None else Path(static_root).resolve()
    if root is not None and not root.is_dir():
        raise ValueError("static_root must be an existing directory")
    by_id = {module.module_id: module for module in modules}
    active: dict[str, Any] = {
        "module_id": modules[0].module_id, "preview": False,
        "profile_id": None, "lesson_sample": False, "preview_return_selection": None,
        "review": False,
        "preferred_profile_id": None,
    }
    selected_profiles: dict[str, str] = {}
    preview_controllers: dict[tuple[str, str | None, bool], DemoController] = {}
    review_controllers: dict[tuple[str, str | None], DemoController] = {}

    def _diagnostics() -> dict[str, DiagnosticSession]:
        return {
            f"{module.module_id}/{profile_id}": runtime.diagnostic
            for module in modules
            for profile_id, runtime in (
                module.profiles.items() if module.profiles else
                (("default", ProfileRuntime(module.controller, module.diagnostic)),)
            )
            if runtime.diagnostic is not None
        }

    if selection_path is not None and selection_path.is_file():
        saved = json.loads(selection_path.read_text(encoding="utf-8"))
        selected_profiles.update({
            module_id: profile_id for module_id, profile_id in saved.get("profiles", {}).items()
            if module_id in by_id and profile_id in by_id[module_id].profiles
        })
        module_id = saved.get("module_id")
        if module_id in by_id:
            active["module_id"] = module_id
            active["profile_id"] = selected_profiles.get(module_id)
        if saved.get("preferred_profile_id") in {"general", "medical"}:
            active["preferred_profile_id"] = saved["preferred_profile_id"]
        for key, diagnostic in _diagnostics().items():
            record = saved.get("diagnostics", {}).get(key, {})
            if (record.get("pack_id"), record.get("version")) != (
                diagnostic.pack.pack_id, diagnostic.pack.version,
            ):
                continue
            if record.get("started") is True:
                diagnostic.start()
                for response in record.get("responses", []):
                    diagnostic.respond(request_id=response["request_id"], option_id=response["option_id"])

    # Allocate the event-loop owner only after fallible persisted-state replay.
    runner = asyncio.Runner()

    def _save_selection() -> None:
        if selection_path is None or active["preview"] or active["lesson_sample"]:
            return
        saved = {
            "module_id": active["module_id"], "profiles": selected_profiles,
            "preferred_profile_id": active["preferred_profile_id"],
            "diagnostics": {
                key: {
                    "pack_id": diagnostic.pack.pack_id, "version": diagnostic.pack.version,
                    "started": diagnostic.view()["status"] != "not_started",
                    "responses": [
                        {"request_id": response.request_id, "option_id": response.option_id}
                        for response in diagnostic.responses
                    ],
                }
                for key, diagnostic in _diagnostics().items()
            },
        }
        selection_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = selection_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(saved), encoding="utf-8")
        temporary.replace(selection_path)

    def _normal_runtime(module: ModuleRuntime) -> ProfileRuntime:
        # Directory status and prerequisite checks use the audience being viewed.
        profile_id = active["profile_id"]
        if profile_id not in module.profiles:
            profile_id = selected_profiles.get(module.module_id, "general")
        return module.profiles.get(profile_id, ProfileRuntime(module.controller, module.diagnostic))

    def _course_controller() -> DemoController:
        module = by_id[active["module_id"]]
        if active["lesson_sample"]:
            return module.lesson_samples[active["profile_id"]]
        runtime = module.profiles.get(active["profile_id"])
        return module.controller if runtime is None else runtime.controller

    def _selected_controller() -> DemoController:
        selected = _course_controller()
        if not active["preview"]:
            if active["review"]:
                return review_controllers[(active["module_id"], active["profile_id"])]
            return selected
        key = (active["module_id"], active["profile_id"], active["lesson_sample"])
        if key not in preview_controllers:
            preview_controllers[key] = DemoController(
                selected.pack, mode="guarded_tutor", profile_id=selected.profile_id,
                teaching_pack=selected.teaching_pack,
            )
        return preview_controllers[key]

    def _selected_diagnostic() -> DiagnosticSession | None:
        if active["preview"] or active["lesson_sample"] or active["review"]:
            return None
        module = by_id[active["module_id"]]
        runtime = module.profiles.get(active["profile_id"])
        return module.diagnostic if runtime is None else runtime.diagnostic

    def _module_status(module: ModuleRuntime) -> str:
        controller = _normal_runtime(module).controller
        state = controller.view()
        completed = set(state.get("completed_activity_ids", ()))
        if state["status"] == "completed" and {
            item.activity_id for item in controller.pack.activities
        }.issubset(completed):
            return "completed"
        unmet = [
            prerequisite_id
            for prerequisite_id in module.prerequisite_module_ids
            if _module_status(by_id[prerequisite_id]) != "completed"
        ]
        return "locked" if unmet and not open_modules else "available"

    def _review_topic(concept_id: str) -> None:
        course = _course_controller()
        course_state = course.view()
        if active["preview"] or active["lesson_sample"] or (
            course_state["status"] != "completed"
            and concept_id not in course_state.get("topic_practice_completed_concept_ids", ())
        ):
            raise ValueError("complete the topic's learning questions before reviewing it")
        activity_ids = course.topic_activity_ids(concept_id)
        if not activity_ids:
            raise ValueError("unknown concept_id")
        key = (active["module_id"], active["profile_id"])
        if active["review"]:
            current = review_controllers[key].view()
            if current.get("activity_concept_id") == concept_id:
                return
        review = DemoController(
            course.pack, mode="guarded_tutor", profile_id=course.profile_id,
            teaching_pack=course.teaching_pack,
        )
        review.start(
            session_id=f"review.{uuid4().hex}",
            preferred_activity_ids=activity_ids, route_scope="preferred",
        )
        review_controllers[key] = review
        active["review"] = True

    def _open_final_check(request_id: str) -> None:
        """Resume normal finals, navigate unfinished ones, or review without credit."""

        if active["preview"] or active["lesson_sample"]:
            raise ValueError("return to the normal course before opening its final check")
        course = _course_controller()
        course_state = course.view()
        activity_ids = course.final_activity_ids()
        if not activity_ids:
            raise ValueError("this course has no final check")
        if course_state["status"] == "not_started":
            raise ValueError("start the course before opening its final check")
        if course_state.get("activity_id") in activity_ids:
            # A topic review must not replace an already-open final attempt.
            active["review"] = False
            return
        if course_state["status"] == "active" and not set(activity_ids).issubset(
            course_state.get("completed_activity_ids", ())
        ):
            course.navigate_to_final_check(request_id=request_id)
            active["review"] = False
            return
        key = (active["module_id"], active["profile_id"])
        if active["review"]:
            current = review_controllers[key].view()
            if tuple(current.get("preferred_activity_ids", ())) == activity_ids:
                return
        review = DemoController(course.pack, mode="guarded_tutor", profile_id=course.profile_id,
                                teaching_pack=course.teaching_pack)
        review.start(session_id=f"review.final.{uuid4().hex}",
                     preferred_activity_ids=activity_ids, route_scope="preferred")
        review_controllers[key] = review
        active["review"] = True

    def _registry_view() -> list[dict[str, Any]]:
        return [
            {
                "module_id": module.module_id,
                "title": module.title,
                "optional": module.optional,
                "prerequisite_module_ids": list(module.prerequisite_module_ids),
                "nirvana_task": module.nirvana_task,
                "status": "available" if active["preview"] else _module_status(module),
                "practical_mission": _practical_mission(module.controller),
                **({"intent": module.introductions[
                    active["profile_id"] if active["profile_id"] in module.introductions else "general"
                ].comparison.this_course_question} if module.introductions else {}),
            }
            for module in modules
        ]

    def _hub_state() -> dict[str, Any]:
        active_module = by_id[active["module_id"]]
        controller = _selected_controller()
        state = _state(controller, _selected_diagnostic(), model)
        state["active_module_id"] = active_module.module_id
        state["modules"] = _registry_view()
        state["course_title"] = active_module.title
        introduction = None if active_module.introductions is None else active_module.introductions.get(
            active["profile_id"] or "general",
        )
        state["course_introduction"] = None if introduction is None else introduction.model_dump(mode="json")
        state["preview_mode"] = active["preview"]
        state["review_mode"] = active["review"] and not active["preview"]
        state["review_available"] = (
            not active["preview"] and not active["lesson_sample"]
            and _course_controller().view()["status"] == "completed"
        )
        state["profile_id"] = active["profile_id"]
        state["course_profiles"] = list(active_module.profiles)
        state["profile_required"] = bool(
            active_module.profiles and active["profile_id"] is None
            and not active["lesson_sample"]
        )
        state["profile_content_version"] = (
            controller.teaching_pack.version if active["profile_id"] is not None else None
        )
        state["learning_pack_id"] = controller.pack.pack_id
        state["learning_pack_version"] = controller.pack.version
        state["lesson_is_sample"] = active["lesson_sample"]
        state["lesson_profiles"] = list(active_module.lesson_samples)
        from .lesson_samples import lesson_view
        activity = next((item for item in controller.pack.activities if item.activity_id == state.get("activity_id")), None)
        state["activity_is_transfer"] = bool(activity and activity.is_transfer)
        state["activity_stage"] = None if activity is None else ("challenge" if activity.is_transfer else "practice")
        if getattr(controller.teaching_pack, "lessons", ()):
            state["lesson"] = None if activity is None else lesson_view(controller.teaching_pack, activity.concept_id)
        else:
            state["lesson"] = lesson_view(controller.teaching_pack)
        state["preview_activities"] = [
            {"activity_id": item.activity_id, "concept_id": item.concept_id,
             "title": f"{item.concept_id.replace('-', ' ').capitalize()} · {'challenge' if item.is_transfer else 'practice'}"}
            for item in controller.pack.activities
        ] if active["preview"] else []
        if active["preview"]:
            state["completed_concept_ids"] = ()
            state["completed_activity_ids"] = ()
            state["topic_practice_completed_concept_ids"] = ()
        elif active["review"]:
            course = _course_controller().view()
            for key in ("completed_concept_ids", "completed_activity_ids", "topic_practice_completed_concept_ids", "m1_ready_concept_ids"):
                state[key] = course.get(key, ())
            state["final_check_activity_ids"] = course.get("final_check_activity_ids", [])
            saved_final = course.get("final_check")
            if saved_final is not None:
                selected_final = state.get("final_check")
                state["final_check"] = {**saved_final,
                    "is_current": bool(selected_final and selected_final["is_current"])}
        _save_selection()
        return state

    class HubHandler(_HubTransport):
        _static_root = root

        def do_GET(self) -> None:  # noqa: N802 - required stdlib handler name
            path = urlparse(self.path).path
            if path == "/authoring/content-pack-editor.html" and host == "127.0.0.1":
                page = _authoring_page(self.client_address[0])
                if page is not None:
                    self._html(page)
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            elif path == "/api/state":
                self._json(HTTPStatus.OK, _hub_state())
            elif path == "/api/modules":
                self._json(
                    HTTPStatus.OK,
                    {"modules": _registry_view(), "active_module_id": active["module_id"]},
                )
            elif path == "/api/trace":
                self._json(HTTPStatus.OK, _selected_controller().developer_trace())
            else:
                self._static(path)

        def do_POST(self) -> None:  # noqa: N802 - required stdlib handler name
            path = urlparse(self.path).path
            request_id = f"http.{uuid4().hex}"
            try:
                body = self._body()
                request_id = body.get("request_id") or request_id
                if path == "/api/validate-content-pack":
                    self._json(HTTPStatus.OK, _validate_content_pack(body["pack"]))
                    return
                if path == "/api/preview":
                    if not isinstance(body.get("enabled"), bool):
                        raise ValueError("preview enabled must be a boolean")
                    if body["enabled"] and not active["preview"]:
                        active["preview_return_selection"] = (
                            active["module_id"], active["profile_id"], active["lesson_sample"], active["review"],
                        )
                    elif not body["enabled"] and active["preview"]:
                        active["module_id"], active["profile_id"], active["lesson_sample"], active["review"] = active["preview_return_selection"]
                        active["preview_return_selection"] = None
                    active["preview"] = body["enabled"]
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/preview/navigate":
                    if not active["preview"]:
                        raise ValueError("enter testing preview before opening an arbitrary activity")
                    previous = _selected_controller()
                    activity_id = body["activity_id"]
                    if not any(item.activity_id == activity_id for item in previous.pack.activities):
                        raise ValueError("unknown activity_id")
                    preview = DemoController(
                        previous.pack, mode="guarded_tutor", profile_id=previous.profile_id,
                        teaching_pack=previous.teaching_pack,
                    )
                    preview.start(session_id=f"preview.{uuid4().hex}", preferred_activity_ids=(activity_id,), route_scope="preferred")
                    preview_controllers[(active["module_id"], active["profile_id"], active["lesson_sample"])] = preview
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/select-profile":
                    module = by_id[active["module_id"]]
                    profile_id = body.get("profile_id")
                    if profile_id not in module.profiles:
                        raise ValueError("choose an available course profile")
                    active["profile_id"] = profile_id
                    active["lesson_sample"] = False
                    active["review"] = False
                    if not active["preview"]:
                        selected_profiles[module.module_id] = profile_id
                        active["preferred_profile_id"] = profile_id
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/start-lesson":
                    profile_id = body.get("profile_id")
                    module = by_id[active["module_id"]]
                    if profile_id not in module.lesson_samples:
                        raise ValueError("choose an available lesson profile")
                    active["profile_id"] = profile_id
                    active["lesson_sample"] = True
                    active["review"] = False
                    controller = _selected_controller()
                    controller.start(session_id=f"lesson.{profile_id}.{controller.pack.version}")
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/select-module":
                    target_id = body.get("module_id")
                    if target_id not in by_id:
                        raise ValueError("unknown module_id")
                    # `test_only_force_unlock` deliberately bypasses the prerequisite
                    # check. It exists only so a developer can reach a locked module
                    # without replaying its prerequisites; it is not exposed as normal
                    # product behavior and does not alter any module's own completion
                    # state or event history.
                    if (
                        not active["preview"] and _module_status(by_id[target_id]) == "locked"
                        and body.get("test_only_force_unlock") is not True
                    ):
                        raise ValueError("module is locked until its prerequisites are completed")
                    active["module_id"] = target_id
                    preferred_profile = active["preferred_profile_id"]
                    active["profile_id"] = (
                        preferred_profile if preferred_profile in by_id[target_id].profiles
                        else selected_profiles.get(target_id)
                    )
                    if active["profile_id"] is not None and not active["preview"]:
                        selected_profiles[target_id] = active["profile_id"]
                    active["lesson_sample"] = False
                    active["review"] = False
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                active_module = by_id[active["module_id"]]
                if active_module.profiles and active["profile_id"] is None and not active["preview"]:
                    raise ValueError("course profile selection is not ready; choose a profile first")
                if path == "/api/review-topic":
                    _review_topic(body.get("concept_id"))
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/final-check":
                    request_id = body.get("request_id")
                    if not isinstance(request_id, str) or not request_id.strip():
                        raise ValueError("request_id is required")
                    _open_final_check(request_id)
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/navigate" and not active["preview"] and not active["lesson_sample"]:
                    concept_id = body.get("concept_id")
                    course = _course_controller()
                    if not course.topic_activity_ids(concept_id):
                        raise ValueError("unknown concept_id")
                    if concept_id in course.view().get("topic_practice_completed_concept_ids", ()):
                        _review_topic(concept_id)
                        self._json(HTTPStatus.OK, _hub_state())
                        return
                    # Leaving a temporary review resumes the saved course before
                    # navigating; review scores never become course credit.
                    active["review"] = False
                if path == "/api/end-review":
                    active["review"] = False
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/reset" and active_module.profiles and not active["preview"]:
                    controller = _course_controller()
                    if (body.get("profile_id"), body.get("pack_id"), body.get("version")) != (
                        active["profile_id"], controller.pack.pack_id, controller.pack.version,
                    ):
                        raise ValueError("profile reset is not ready; refresh the selected profile and pack version")
                    controller.reset()
                    active["review"] = False
                    diagnostic = _selected_diagnostic()
                    if diagnostic is not None:
                        diagnostic.reset()
                    selected_profiles.pop(active_module.module_id, None)
                    review_controllers.pop((active["module_id"], active["profile_id"]), None)
                    active["profile_id"] = None
                    active["lesson_sample"] = False
                    active["review"] = False
                    self._json(HTTPStatus.OK, _hub_state())
                    return
                if path == "/api/reset" and not active["preview"]:
                    active["review"] = False
                    review_controllers.pop((active["module_id"], active["profile_id"]), None)
                if active_module.profiles and not active["lesson_sample"] and path in {
                    "/api/start", "/api/diagnostic/skip", "/api/start-scene",
                }:
                    controller = _selected_controller()
                    # Preview can use the module's General controller before an
                    # explicit profile choice; its fixed audience owns identity.
                    profile_id = controller.profile_id or "general"
                    body.setdefault("session_id", f"course.{active_module.module_id}.{profile_id}.{controller.pack.version}")
                result = runner.run(
                    _handle_command(
                        _selected_controller(),
                        path,
                        body,
                        model=model,
                        diagnostic=_selected_diagnostic(),
                        unguarded_tutor=unguarded_tutor,
                    )
                )
                if active["review"] and not active["preview"] and result["status"] == "completed":
                    active["review"] = False
                self._json(HTTPStatus.OK, _hub_state())
            except Exception as exc:
                status, failure = _request_failure(exc, str(request_id))
                upstream = failure.get("upstream_status")
                detail = "" if upstream is None else f"; upstream HTTP {upstream}"
                print(f"Request {request_id} to {path} failed ({type(exc).__name__}{detail}).",
                      file=sys.stderr, flush=True)
                self._json(status, failure)

    closed = False

    def close() -> None:
        nonlocal closed
        if closed:
            return
        closed = True
        try:
            if close_model:
                client = getattr(model, "client", None)
                if client is not None and hasattr(client, "close"):
                    runner.run(client.close())
        finally:
            runner.close()

    return HubHandler, close


async def _handle_command(
    controller: DemoController,
    path: str,
    body: dict[str, Any],
    *,
    model: Model | str,
    diagnostic: DiagnosticSession | None = None,
    unguarded_tutor: bool = False,
) -> dict[str, Any]:
    if path == "/api/diagnostic/start":
        if diagnostic is None:
            raise ValueError("diagnostic is not configured")
        diagnostic.start()
        return _state(controller, diagnostic, model)
    if path == "/api/diagnostic/respond":
        if diagnostic is None:
            raise ValueError("diagnostic is not configured")
        diagnostic.respond(request_id=body["request_id"], option_id=body["option_id"])
        return _state(controller, diagnostic, model)
    if path == "/api/diagnostic/skip":
        # Starting the full route persists the opt-out in the existing session
        # event; it does not fabricate diagnostic responses or completion.
        await controller.start_with_tutor(
            session_id=body.get("session_id", "demo.session.01"),
            preferred_activity_ids=(),
            route_scope="all",
            model=model,
        )
        return _state(controller, diagnostic, model)
    if path == "/api/start":
        _require_learning_unlocked(controller, diagnostic)
        preferred = _preferred_activities(diagnostic)
        await controller.start_with_tutor(
            session_id=body.get("session_id", "demo.session.01"),
            preferred_activity_ids=preferred,
            route_scope=("preferred" if diagnostic is not None else "all"),
            model=model,
        )
        return _state(controller, diagnostic, model)
    if path == "/api/start-scene":
        mission = _practical_mission(controller)
        if mission is None:
            raise ValueError("this module has no practical mission; start its learning activities instead")
        await controller.start_with_tutor(
            session_id=body.get("session_id", "demo.scene.01"),
            preferred_activity_ids=(mission["activity_id"],),
            route_scope="preferred",
            model=model,
        )
        return _state(controller, diagnostic, model)
    if path == "/api/respond":
        _require_learning_unlocked(controller, diagnostic)
        controller.respond(
            request_id=body["request_id"],
            option_id=body["option_id"],
        )
        return _state(controller, diagnostic, model)
    if path == "/api/message":
        _require_learning_unlocked(controller, diagnostic)
        await controller.send_message_with_tutor(
            request_id=body["request_id"],
            text=body["text"],
            model=model,
            unguarded=unguarded_tutor,
        )
        return _state(controller, diagnostic, model)
    if path == "/api/experiment-action":
        _require_learning_unlocked(controller, diagnostic)
        input_revision = body["input_revision"]
        if type(input_revision) is not int:
            raise ValueError("input_revision must be an integer")
        controller.submit_experiment_action(
            request_id=body["request_id"], attempt_id=body["attempt_id"],
            experiment_id=body["experiment_id"], input_revision=input_revision,
            action=TypeAdapter(ExperimentAction).validate_json(json.dumps(body["action"])),
        )
        return _state(controller, diagnostic, model)
    if path == "/api/scene-action":
        _require_learning_unlocked(controller, diagnostic)
        input_revision = body["input_revision"]
        if not isinstance(input_revision, int) or isinstance(input_revision, bool):
            raise ValueError("input_revision must be an integer")
        await controller.submit_scene_action_with_tutor(
            request_id=body["request_id"],
            input_revision=input_revision,
            # JSON has arrays, while the immutable internal contract uses tuples.
            # `strict=False` is limited to this transport decoding boundary; the
            # tagged action and every field remain fully validated afterwards.
            action=TypeAdapter(CausalSceneAction).validate_python(
                body["action"], strict=False
            ),
            model=model,
        )
        return _state(controller, diagnostic, model)
    if path == "/api/scene-evidence":
        _require_learning_unlocked(controller, diagnostic)
        await controller.submit_scene_evidence_with_tutor(
            request_id=body["request_id"], model=model
        )
        return _state(controller, diagnostic, model)
    if path == "/api/explain":
        _require_learning_unlocked(controller, diagnostic)
        await controller.request_explanation_with_tutor(
            request_id=body["request_id"], model=model
        )
        return _state(controller, diagnostic, model)
    if path == "/api/continue":
        _require_learning_unlocked(controller, diagnostic)
        await controller.continue_activity_with_tutor(
            request_id=body["request_id"], model=model
        )
        return _state(controller, diagnostic, model)
    if path == "/api/navigate":
        _require_learning_unlocked(controller, diagnostic)
        await controller.navigate_to_concept_with_tutor(
            request_id=body["request_id"],
            concept_id=body["concept_id"],
            model=model,
        )
        return _state(controller, diagnostic, model)
    if path == "/api/reset":
        controller.reset()
        if diagnostic is not None:
            diagnostic.reset()
        return _state(controller, diagnostic, model)
    raise ValueError("unknown command")


def _state(
    controller: DemoController,
    diagnostic: DiagnosticSession | None,
    model: Model | str,
) -> dict[str, Any]:
    state = controller.view()
    diagnostic_view = None if diagnostic is None else diagnostic.view()
    if diagnostic is not None and diagnostic_view["status"] == "in_progress":
        # Reuse the exact question's presentation overlay, not the diagnostic's
        # scored pack or a profile-wide/lesson image fallback.
        current_id = diagnostic.activities[len(diagnostic.responses)].activity_id
        image = next(item.scenario_image for item in controller.teaching_pack.activities
                     if item.activity_id == current_id)
        diagnostic_view["scenario_image"] = None if image is None else image.model_dump()
    state["diagnostic"] = diagnostic_view
    state["practical_mission"] = _practical_mission(controller)
    # Additive: lets a generic (non-M0) client render concept labels/routes
    # without hardcoding a concept list per module.
    state["concepts"] = [
        {"concept_id": concept.concept_id, "objective": concept.objective}
        for concept in controller.pack.concepts
    ]
    state["learning_unlocked"] = (
        diagnostic_view is None
        or diagnostic_view["status"] == "completed"
        or state["status"] in {"active", "completed"}
    )
    state["tutor_status"] = "ready"
    return state


def _require_learning_unlocked(
    controller: DemoController, diagnostic: DiagnosticSession | None
) -> None:
    if (
        diagnostic is not None
        and diagnostic.view()["status"] != "completed"
        and controller.view()["status"] == "not_started"
    ):
        raise ValueError("complete the entry diagnostic before starting M0")


def _preferred_activities(
    diagnostic: DiagnosticSession | None,
) -> tuple[str, ...]:
    """Place diagnostic misses first without treating the diagnostic as M0 credit."""

    if diagnostic is None:
        return ()
    result = diagnostic.view().get("result")
    if not isinstance(result, dict):
        return ()
    concept_results = result.get("concept_results")
    if not isinstance(concept_results, list):
        return ()
    missed_concepts = {
        item.get("concept_id")
        for item in concept_results
        if isinstance(item, dict) and item.get("accepted") is False
    }
    return tuple(
        activity.activity_id
        for activity in diagnostic.pack.activities
        if activity.concept_id in missed_concepts
    )


_FALLBACK_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>EducAgent SDK demo</title></head>
<body><p>Build the Astryx client with <code>npm run web:build</code>, then restart this demo.</p></body></html>"""
