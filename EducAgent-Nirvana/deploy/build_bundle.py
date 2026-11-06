"""Build an allowlisted Linux deployment archive, excluding credentials by default."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile


DEPLOY = Path(__file__).resolve().parent
WORKSPACE = DEPLOY.parents[1]
PUBLIC_SUFFIXES = {".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg",
                   ".ico", ".woff", ".woff2", ".ttf", ".avif"}


def copy_file(source: Path, target: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"required regular source file is missing: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def copy_tree(source: Path, target: Path, suffixes: set[str]) -> None:
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"required regular source directory is missing: {source.name}")
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source)
        if item.is_symlink():
            raise ValueError("deployment sources must not contain filesystem links")
        if item.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            if item.suffix.lower() in suffixes:
                copy_file(item, target / relative)


def stage_bundle(destination: Path, workspace: Path = WORKSPACE, *, env_file: Path | None = None) -> dict:
    """Copy canonical runtime/public sources, never a whole working directory."""
    sdk = workspace / "EducAgent-SDK"
    nirvana = workspace / "EducAgent-Nirvana"
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        copy_file(workspace / name, destination / name)
    for name in ("run.py", "check.py", "nginx.conf.template", "Dockerfile", "compose.yaml",
                 ".dockerignore", "constraints.txt", "README.md", "config/elm.env.example",
                 "systemd/educagent.service"):
        copy_file(DEPLOY / name, destination / name)
    for name in ("pyproject.toml", "README.md", "examples/playable_demo.py"):
        copy_file(sdk / name, destination / "EducAgent-SDK" / name)
    copy_tree(sdk / "src/educagent_sdk", destination / "EducAgent-SDK/src/educagent_sdk", {".py"})
    registry = json.loads((sdk / "content/modules.json").read_text(encoding="utf-8"))
    content_paths = {"content/modules.json", "content/course_introductions.json", "content/course_illustrations.json"}
    for module in registry["modules"]:
        content_paths.add(module["pack_path"])
        content_paths.update(module["profile_pack_paths"].values())
        if module.get("diagnostic_path"):
            content_paths.add(module["diagnostic_path"])
    for name in sorted(content_paths):
        source = (sdk / name).resolve()
        if sdk.resolve() not in source.parents or source.suffix != ".json":
            raise ValueError("module registry references an unsafe content path")
        copy_file(source, destination / "EducAgent-SDK" / name)
    copy_file(nirvana / "demo_server.py", destination / "EducAgent-Nirvana/demo_server.py")
    site = destination / "site"
    for name in ("index.html", "styles.css"):
        copy_file(workspace / name, site / name)
    copy_file(sdk / "web/dist/sources.html", site / "sources.html")
    copy_tree(sdk / "web/dist", site / "portal", PUBLIC_SUFFIXES)
    copy_tree(sdk / "web/dist/media", site / "media", PUBLIC_SUFFIXES)
    copy_tree(nirvana / "demo", site / "nirvana", PUBLIC_SUFFIXES)
    # The local Windows launcher keeps its separate API; only this bundle is same-origin.
    (site / "nirvana/config.js").write_text('window.NIRVANA_API_BASE = "/nirvana/api";\n', encoding="utf-8")
    provenance = sdk / "web/public/media/foundation-samples/README.md"
    if provenance.is_file():
        copy_file(provenance, destination / "ASSET-PROVENANCE.md")
    openings = sdk / "web/public/media/course-openings/README.md"
    if openings.is_file():
        copy_file(openings, destination / "COURSE-OPENING-PROVENANCE.md")
    questions = sdk / "web/public/media/question-context/README.md"
    if questions.is_file():
        copy_file(questions, destination / "QUESTION-ILLUSTRATION-PROVENANCE.md")
    katex_license = sdk / "node_modules/katex/LICENSE"
    if katex_license.is_file():
        copy_file(katex_license, destination / "licenses/KaTeX-LICENSE")
    copy_file(DEPLOY / "licenses/micromark-LICENSE", destination / "licenses/micromark-LICENSE")
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Private expert review with anonymous browser-session isolation; no user accounts",
        "entry_port": 9090,
        "contains_credentials": env_file is not None,
        "courses": [{"module_id": module["module_id"], "profiles": {
            profile: {key: pack[key] for key in ("pack_id", "version")}
            for profile, filename in module["profile_pack_paths"].items()
            for pack in [json.loads((sdk / filename).read_text(encoding="utf-8"))]
        }} for module in registry["modules"]],
        "files": {item.relative_to(destination).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
                  for item in sorted(destination.rglob("*")) if item.is_file()},
    }
    (destination / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if env_file is not None:
        # Keep the live secret out of the image/integrity manifest. Compose reads
        # it on the host; .dockerignore excludes it from the image build context.
        target = destination / "config/elm.env"
        copy_file(env_file, target)
        target.chmod(0o600)
    return manifest


def archive_bundle(staged: Path, archive: Path) -> None:
    with tarfile.open(archive, "w:gz") as output:
        for path in sorted(staged.rglob("*")):
            if not path.is_file():
                continue
            name = staged.name + "/" + path.relative_to(staged).as_posix()
            info = output.gettarinfo(str(path), arcname=name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o600 if path.relative_to(staged).as_posix() == "config/elm.env" else 0o644
            with path.open("rb") as stream:
                output.addfile(info, stream)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    if (staged / "config/elm.env").exists():
        archive.chmod(0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=WORKSPACE / "output")
    parser.add_argument("--name", default=None)
    parser.add_argument("--skip-build", action="store_true", help="Use an already checked web/dist build.")
    parser.add_argument("--include-env", action="store_true", help="Include the local SDK .env in a PRIVATE archive; never share it publicly.")
    args = parser.parse_args()
    args.name = args.name or f"educagent-server-{date.today():%Y%m%d}" + ("-private" if args.include_env else "")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", args.name):
        parser.error("name must be one plain filename, without directories")
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output.resolve() / f"{args.name}.tar.gz"
    if archive.exists():
        parser.error("archive already exists; choose a new --name to preserve it")
    if not args.skip_build:
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        if npm is None:
            parser.error("npm is required on the packaging workstation, not on the server")
        for task in ("web:check", "web:build"):
            subprocess.run([npm, "run", task], cwd=WORKSPACE / "EducAgent-SDK", check=True)
    with tempfile.TemporaryDirectory(prefix="educagent-package-", dir=args.output) as temporary:
        staged = Path(temporary) / args.name
        staged.mkdir()
        manifest = stage_bundle(staged, env_file=WORKSPACE / "EducAgent-SDK/.env" if args.include_env else None)
        archive_bundle(staged, archive)
    print(f"Created {archive} ({archive.stat().st_size:,} bytes, {len(manifest['files'])} files)")
    print("PRIVATE: contains server credentials; transfer only via SSH/SCP."
          if args.include_env else "No local credentials were packaged.")
    print("No progress traces or textbook PDFs were packaged.")


if __name__ == "__main__":
    main()
