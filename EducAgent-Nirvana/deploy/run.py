"""Run the private EducAgent review bundle behind one Nginx entrance."""

from __future__ import annotations

import argparse
import ipaddress
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
PORTAL_PORT = 9091
NIRVANA_PORT = 9092


def render_nginx(template: str, *, site: Path, runtime: Path, bind: str) -> str:
    """Render trusted paths only; never interpolate credentials into Nginx."""
    for path in (site, runtime):
        if any(char in str(path) for char in ('"', "\n", "\r", "$")):
            raise ValueError("deployment paths must not contain quotes, newlines or dollar signs")
    address = ipaddress.IPv4Address(bind)
    return (template.replace("__SITE__", site.resolve().as_posix())
            .replace("__RUNTIME__", runtime.resolve().as_posix())
            .replace("__BIND__", str(address)))


def commands(env_file: Path, data: Path, nginx: str, config: Path, *, secure_cookie: bool = False) -> list[list[str]]:
    result = [
        [sys.executable, str(ROOT / "EducAgent-SDK/examples/playable_demo.py"),
         "--port", str(PORTAL_PORT), "--static-root", str(ROOT / "site"),
         "--events-root", str(data / "portal"), "--env-file", str(env_file),
         "--unguarded-tutor"],
        [sys.executable, str(ROOT / "EducAgent-Nirvana/demo_server.py"),
         "--port", str(NIRVANA_PORT), "--origin-port", "9090", "--env-file", str(env_file)],
        [nginx, "-e", "stderr", "-p", str(config.parent) + os.sep, "-c", str(config), "-g", "daemon off;"],
    ]
    if secure_cookie:
        result[0].append("--secure-session-cookie")
    return result


def stop_children(children: list[subprocess.Popen]) -> None:
    # Only terminate processes created by this invocation, never port owners.
    for child in reversed(children):
        if child.poll() is None:
            child.terminate()
    for child in reversed(children):
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def request_stop(*_args: object) -> None:
    raise KeyboardInterrupt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default=os.environ.get("BIND_HOST", "127.0.0.1"))
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("DATA_DIR", ROOT / "data")))
    parser.add_argument("--env-file", type=Path, default=ROOT / "config/elm.env")
    parser.add_argument("--check-config", action="store_true", help="Validate locally without contacting ELM.")
    parser.add_argument("--secure-session-cookie", action="store_true", default=os.environ.get("SESSION_COOKIE_SECURE") == "1")
    args = parser.parse_args()
    children: list[subprocess.Popen] = []
    try:
        from educagent_sdk.elm import load_elm_settings

        settings = load_elm_settings(args.env_file)
        if settings.model_name == "CHANGE_ME" or settings.api_key == "CHANGE_ME":
            raise ValueError("replace MODEL and ELM_API_KEY in config/elm.env before starting")
        nginx = shutil.which("nginx")
        if nginx is None:
            raise ValueError("Nginx is not installed or not in PATH; see README.md")
        data = args.data_dir.resolve()
        runtime = data / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        (data / "portal").mkdir(parents=True, exist_ok=True)
        site = ROOT / "site"
        if not (site / "portal/index.html").is_file() or not (site / "nirvana/index.html").is_file():
            raise ValueError("built public files are missing; run the extracted deployment bundle")
        config = runtime / "nginx.conf"
        config.write_text(render_nginx((ROOT / "nginx.conf.template").read_text(encoding="utf-8"),
                                      site=site, runtime=runtime, bind=args.bind), encoding="utf-8")
        subprocess.run([nginx, "-t", "-e", "stderr", "-p", str(runtime) + os.sep, "-c", str(config)], check=True)
        if args.check_config:
            print("Configuration valid. No ELM request was made.")
            return 0
        # Fail before starting anything if another service owns a required port.
        for address, port in ((args.bind, 9090), ("127.0.0.1", PORTAL_PORT), ("127.0.0.1", NIRVANA_PORT)):
            with socket.socket() as probe:
                probe.bind((address, port))
        signal.signal(signal.SIGTERM, request_stop)
        child_env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        for command in commands(args.env_file.resolve(), data, nginx, config, secure_cookie=args.secure_session_cookie):
            children.append(subprocess.Popen(command, cwd=ROOT, env=child_env))
        print(f"EducAgent entrance: http://{args.bind}:9090/", flush=True)
        print("Private review instance: Portal progress/reset is isolated by anonymous browser cookie.", flush=True)
        while True:
            for index, child in enumerate(children):
                if child.poll() is not None:
                    print(f"Service {('Portal', 'Nirvana', 'Nginx')[index]} stopped (exit {child.returncode}).", file=sys.stderr)
                    return 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    except (ImportError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Startup failed: {exc}", file=sys.stderr)
        return 1
    finally:
        stop_children(children)


if __name__ == "__main__":
    raise SystemExit(main())
