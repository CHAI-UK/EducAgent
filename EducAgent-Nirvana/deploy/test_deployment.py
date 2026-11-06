"""Provider-independent checks for the shared-server distribution contract."""

import hashlib
import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest

import build_bundle
import check
import run


class DeploymentTests(unittest.TestCase):
    def test_six_packaged_profiles_load_without_development_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "bundle"
            root.mkdir()
            build_bundle.stage_bundle(root)
            source = root / "EducAgent-SDK/examples/playable_demo.py"
            spec = importlib.util.spec_from_file_location("bundled_playable_demo", source)
            demo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(demo)
            introductions = demo.load_course_introductions(root / "EducAgent-SDK/content/course_introductions.json")
            illustrations = demo.load_course_illustrations(root / "EducAgent-SDK/content/course_illustrations.json")
            modules = [demo._build_module(entry, events_root=root / "data/portal", reset=False,
                                         introduction_catalog=introductions, illustration_catalog=illustrations)
                       for entry in demo._load_registry(root / "EducAgent-SDK/content/modules.json")]
            self.assertEqual(len(modules), 3)
            self.assertTrue(all(set(module.profiles) == {"general", "medical"} for module in modules))
            self.assertTrue(all(path.stat().st_size == 0 for path in (root / "data/portal").glob("*.jsonl")))
            for image in illustrations.images.values():
                self.assertTrue((root / "site" / image.path).is_file(), image.path)
            self.assertTrue((root / "QUESTION-ILLUSTRATION-PROVENANCE.md").is_file())

    def test_bundle_uses_only_runtime_and_public_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "educagent-test"
            root.mkdir()
            manifest = build_bundle.stage_bundle(root)
            self.assertEqual(len(manifest["courses"]), 3)
            self.assertEqual(sum(len(course["profiles"]) for course in manifest["courses"]), 6)
            names = manifest["files"]
            for notice in ("LICENSE", "THIRD_PARTY_NOTICES.md", "licenses/micromark-LICENSE"):
                self.assertIn(notice, names)
            for name in names:
                self.assertNotIn(".educagent-demo", name)
                self.assertNotIn("node_modules", name)
                self.assertFalse(name.endswith((".jsonl", ".pdf", ".log", ".map")), name)
                self.assertNotIn(".git/", name)
                self.assertNotEqual(Path(name).name, ".env")
                if name.startswith("site/"):
                    self.assertIn(Path(name).suffix, build_bundle.PUBLIC_SUFFIXES)
            self.assertIn('"/nirvana/api"', (root / "site/nirvana/config.js").read_text())
            self.assertEqual(check.verify_bundle(root), len(names))
            config = root / "config/elm.env.example"
            config.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "integrity"):
                check.verify_bundle(root)

    def test_tar_members_are_relative_regular_files_and_checksum_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "educagent-test"
            root.mkdir()
            (root / "sample.txt").write_text("sample", encoding="utf-8")
            archive = Path(temporary) / "test.tar.gz"
            build_bundle.archive_bundle(root, archive)
            with tarfile.open(archive) as stream:
                self.assertEqual(stream.getnames(), ["educagent-test/sample.txt"])
                self.assertTrue(all(member.isfile() and member.mode == 0o644 for member in stream))
            self.assertTrue(archive.with_name("test.tar.gz.sha256").read_text().startswith(
                hashlib.sha256(archive.read_bytes()).hexdigest()))

    def test_explicit_private_bundle_keeps_secret_out_of_image_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            secret = base / "test.env"
            secret.write_text("ELM_API_KEY=disposable-test-value\n", encoding="utf-8")
            root = base / "private-bundle"
            root.mkdir()
            manifest = build_bundle.stage_bundle(root, env_file=secret)
            self.assertTrue(manifest["contains_credentials"])
            self.assertNotIn("config/elm.env", manifest["files"])
            self.assertEqual((root / "config/elm.env").read_bytes(), secret.read_bytes())
            self.assertIn("config/elm.env", (root / ".dockerignore").read_text())
            archive = base / "private.tar.gz"
            build_bundle.archive_bundle(root, archive)
            with tarfile.open(archive) as stream:
                self.assertEqual(stream.getmember("private-bundle/config/elm.env").mode, 0o600)

    def test_nginx_routes_are_same_origin_and_editor_preview_are_blocked(self):
        text = run.render_nginx((build_bundle.DEPLOY / "nginx.conf.template").read_text(),
                                site=Path("site"), runtime=Path("data/runtime"), bind="127.0.0.1")
        self.assertIn("listen 127.0.0.1:9090;", text)
        self.assertIn("proxy_pass http://127.0.0.1:9092/api/;", text)
        self.assertIn("location = /api/validate-content-pack { return 404; }", text)
        self.assertIn("location ^~ /authoring/ { return 404; }", text)
        self.assertIn("location = /api/preview { return 404; }", text)
        self.assertNotIn("__SITE__", text)
        with self.assertRaises(ValueError):
            run.render_nginx("", site=Path("a$site"), runtime=Path("data"), bind="127.0.0.1")

    def test_launcher_never_resets_or_exposes_python_backends(self):
        commands = run.commands(Path("secret.env"), Path("data"), "nginx", Path("nginx.conf"))
        for command in commands:
            self.assertNotIn("--reset", command)
            self.assertNotIn("--lan", command)
            self.assertNotIn("--lan-address", command)
        self.assertIn("9091", commands[0])
        self.assertIn("9092", commands[1])


if __name__ == "__main__":
    unittest.main()
