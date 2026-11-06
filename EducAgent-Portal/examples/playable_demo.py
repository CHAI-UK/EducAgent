"""Run the accessible EducAgent Portal with anonymous browser-session progress.

Serves every module declared in a module registry (default
``content/modules.json``): the M0 foundation plus its optional,
parallel post-requisite modules. Each module keeps its own JSONL
progress file and its own controller within each browser cookie session;
the learner switches between them with ``/api/select-module``.
"""

import argparse
import json
from pathlib import Path

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.course_introductions import CourseIntroductionCatalog, load_course_introductions
from educagent_sdk.course_illustrations import CourseIllustrationCatalog, load_course_illustrations
from educagent_sdk.diagnostic import DiagnosticSession, load_diagnostic_plan
from educagent_sdk.elm import build_elm_model, load_elm_settings
from educagent_sdk.lesson_samples import load_lesson_samples
from educagent_sdk.release import validate_release
from educagent_sdk.web_demo import ModuleRuntime, ProfileRuntime, create_browser_session_server


ROOT = Path(__file__).resolve().parents[1]


def _load_registry(registry_path: Path) -> list[dict]:
    entries = json.loads(registry_path.read_text(encoding="utf-8"))["modules"]
    return sorted(entries, key=lambda entry: entry["order"])


def _build_module(
    entry: dict, *, events_root: Path, reset: bool,
    introduction_catalog: CourseIntroductionCatalog | None = None,
    illustration_catalog: CourseIllustrationCatalog | None = None,
) -> ModuleRuntime:
    direct_profiles = entry.get("profile_pack_paths")
    if direct_profiles is not None:
        if set(direct_profiles) != {"general", "medical"} or entry.get("profiles_path") is not None:
            raise ValueError("profile_pack_paths requires General and Medical packs without a profile compiler")
        profiles = {}
        plan = (
            None if entry["diagnostic_path"] is None
            else load_diagnostic_plan(ROOT / entry["diagnostic_path"])
        )
        for profile_id, pack_path in direct_profiles.items():
            profile_pack = load_content_pack(ROOT / pack_path)
            validate_release(profile_pack)
            # Retain the established Foundations versioned filenames. Other
            # modules also name the new pack, avoiding old seed trace collisions.
            profile_suffix = "" if profile_id == "general" else f"-{profile_id}"
            event_name = (
                f"{entry['module_id']}{profile_suffix}-{profile_pack.version}.jsonl"
                if entry["module_id"] == "causality_m0"
                else f"{entry['module_id']}-{profile_id}-{profile_pack.pack_id}-{profile_pack.version}.jsonl"
            )
            profile_store = JsonlEventStore(
                events_root / event_name
            )
            if reset:
                profile_store.reset()
            profiles[profile_id] = ProfileRuntime(
                DemoController(
                    profile_pack, store=profile_store, mode="guarded_tutor", profile_id=profile_id,
                    teaching_pack=None if illustration_catalog is None else illustration_catalog.for_pack(profile_pack),
                ),
                None if plan is None else DiagnosticSession(profile_pack, plan),
            )
        if profiles["general"].controller.pack.concepts != profiles["medical"].controller.pack.concepts:
            raise ValueError("course profiles must preserve the same curriculum and completion requirements")
        return ModuleRuntime(
            module_id=entry["module_id"], title=entry["title"], optional=entry["optional"],
            prerequisite_module_ids=tuple(entry["prerequisite_module_ids"]),
            nirvana_task=entry["nirvana_task"], controller=profiles["general"].controller,
            diagnostic=profiles["general"].diagnostic,
            profiles=profiles,
            introductions=None if introduction_catalog is None else introduction_catalog.for_module(
                entry["module_id"], entry["title"],
                {profile_id: runtime.controller.pack for profile_id, runtime in profiles.items()},
            ),
        )
    pack = load_content_pack(ROOT / entry["pack_path"])
    events_path = events_root / f"{entry['module_id']}-{pack.version}.jsonl"
    store = JsonlEventStore(events_path)
    if reset:
        store.reset()
    profile_packs = {}
    profile_source = entry.get("profiles_path")
    if profile_source is not None:
        from educagent_sdk.foundation_profiles import load_foundation_profiles
        profile_packs = load_foundation_profiles(pack, ROOT / profile_source)
    controller = DemoController(
        pack, store=store, mode="guarded_tutor",
        profile_id="general" if profile_packs else None,
        teaching_pack=profile_packs.get("general"),
    )
    diagnostic = (
        None
        if entry["diagnostic_path"] is None
        else DiagnosticSession(pack, load_diagnostic_plan(ROOT / entry["diagnostic_path"]))
    )
    lesson_samples: dict[str, DemoController] = {}
    if entry.get("lesson_samples_path") is not None:
        for profile_id, lesson_pack in load_lesson_samples(pack, ROOT / entry["lesson_samples_path"]).items():
            lesson_store = JsonlEventStore(events_root / f"{entry['module_id']}-lesson-{profile_id}-{lesson_pack.version}.jsonl")
            if reset:
                lesson_store.reset()
            lesson_samples[profile_id] = DemoController(lesson_pack, store=lesson_store, mode="guarded_tutor")
    profiles: dict[str, ProfileRuntime] = {}
    if profile_packs:
        profiles["general"] = ProfileRuntime(controller, diagnostic)
        medical_pack = profile_packs["medical"]
        medical_store = JsonlEventStore(events_root / f"{entry['module_id']}-medical-{medical_pack.version}.jsonl")
        if reset:
            medical_store.reset()
        profiles["medical"] = ProfileRuntime(
            DemoController(medical_pack, store=medical_store, mode="guarded_tutor", profile_id="medical"),
            None if diagnostic is None else DiagnosticSession(medical_pack, diagnostic.plan),
        )
    return ModuleRuntime(
        module_id=entry["module_id"],
        title=entry["title"],
        optional=entry["optional"],
        prerequisite_module_ids=tuple(entry["prerequisite_module_ids"]),
        nirvana_task=entry["nirvana_task"],
        controller=controller,
        diagnostic=diagnostic,
        lesson_samples=lesson_samples,
        profiles=profiles,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "content" / "modules.json",
        help="Module registry JSON listing the foundation and its post-requisite modules.",
    )
    parser.add_argument(
        "--events-root",
        type=Path,
        default=ROOT / ".educagent-demo",
        help="Private data directory; isolated browser records live under browser-sessions/.",
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--lan", action="store_true", help="Allow explicit LAN access; anonymous browser sessions remain separate.")
    parser.add_argument("--secure-session-cookie", action="store_true", help="Require HTTPS for the session cookie when hosted behind the IT TLS proxy.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="ELM configuration file used by the required guarded tutor.",
    )
    parser.add_argument(
        "--static-root",
        type=Path,
        default=None,
        help="Directory containing the built client (supports /portal/ index routes).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Legacy switch; browser-session progress must be reset from that browser's Portal UI.",
    )
    parser.add_argument(
        "--enforce-module-prerequisites",
        action="store_true",
        help="Require completed prerequisite modules instead of the default open browsing access.",
    )
    parser.add_argument(
        "--unguarded-tutor",
        action="store_true",
        help="Use stage-aware free-text replies in this local demo (legacy flag; not the guarded study policy).",
    )
    args = parser.parse_args()
    if args.reset:
        parser.error("use Reset progress in the intended browser; startup never clears other browser sessions")

    try:
        settings = load_elm_settings(args.env_file)
    except ValueError as exc:
        parser.error(str(exc))

    registry = _load_registry(args.registry)
    introduction_catalog = load_course_introductions(ROOT / "content/course_introductions.json")
    illustration_catalog = load_course_illustrations(ROOT / "content/course_illustrations.json")
    def module_factory(session_directory: Path) -> list[ModuleRuntime]:
        return [
            _build_module(entry, events_root=session_directory, reset=False,
                          introduction_catalog=introduction_catalog,
                          illustration_catalog=illustration_catalog)
            for entry in registry
        ]

    static_root = args.static_root or (ROOT / "web" / "dist")
    server = create_browser_session_server(
        module_factory,
        sessions_root=args.events_root / "browser-sessions",
        host="0.0.0.0" if args.lan else "127.0.0.1",
        allow_lan=args.lan,
        port=args.port,
        model_factory=lambda: build_elm_model(settings),
        secure_cookie=args.secure_session_cookie,
        static_root=static_root if static_root.is_dir() else None,
        unguarded_tutor=args.unguarded_tutor,
        open_modules=not args.enforce_module_prerequisites,
    )
    print(f"Open http://127.0.0.1:{args.port} in a browser. Press Ctrl+C to stop.")
    print(f"Local progress: {args.events_root}")
    print("Progress and preferences follow an anonymous browser session; historical shared records are not imported.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
