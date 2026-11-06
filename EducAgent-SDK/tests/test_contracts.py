import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from educagent_sdk import (
    ContentPack,
    ReleaseValidationError,
    load_content_pack,
    validate_release,
)
from educagent_sdk.contracts import Activity, Choice, Claim, Source, TeachingResource


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0.json"
SCHEMA_PATH = ROOT / "schemas" / "content-pack-v3.schema.json"


def pack_data() -> dict:
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def validate(data: dict) -> ContentPack:
    return ContentPack.model_validate_json(json.dumps(data))


def find_by_id(records: list[dict], field: str, value: str) -> dict:
    return next(record for record in records if record[field] == value)


def release_issues(error: ReleaseValidationError) -> tuple[tuple[str, str], ...]:
    return tuple((issue.path, issue.code) for issue in error.report.issues)


class ContentContractTest(unittest.TestCase):
    def test_seed_pack_loads_as_frozen_v3_contract(self) -> None:
        pack = load_content_pack(PACK_PATH)

        self.assertEqual(pack.schema_version, "3.0")
        self.assertEqual(pack.version, "0.2.0")
        self.assertIsInstance(pack.sources[0], Source)
        self.assertIsInstance(pack.claims[0], Claim)
        self.assertIsInstance(pack.resources[0], TeachingResource)
        self.assertIsInstance(pack.activities[0], Activity)
        self.assertIsInstance(pack.activities[0].choices[0], Choice)
        self.assertIsInstance(pack.resources, tuple)
        with self.assertRaises(ValidationError):
            pack.title = "Changed"
        with self.assertRaises(ValidationError):
            pack.claims[0].proposition = "Changed"
        with self.assertRaises(ValidationError):
            pack.activities[0].choices[0].text = "Changed"

    def test_unknown_fields_fail_at_every_level(self) -> None:
        paths = (
            (),
            ("sources", 0),
            ("claims", 0),
            ("claims", 0, "source_refs", 0),
            ("resources", 0),
            ("activities", 0),
            ("activities", 0, "choices", 0),
        )
        for path in paths:
            with self.subTest(path=path):
                data = pack_data()
                target = data
                for part in path:
                    target = target[part]
                target["unknown"] = "value"
                with self.assertRaises(ValidationError):
                    validate(data)

        data = pack_data()
        claim = data["claims"][0]
        claim["source_refs"] = []
        claim["deterministic_derivation"] = {
            "method_id": "test.method",
            "method_version": "1.0.0",
            "unknown": "value",
        }
        with self.assertRaises(ValidationError):
            validate(data)

    def test_scalar_types_and_enums_are_strict(self) -> None:
        cases = (
            ("schema v1", lambda data: data.__setitem__("schema_version", "1.0")),
            (
                "boolean",
                lambda data: data["activities"][0]["choices"][0].__setitem__(
                    "correct", "true"
                ),
            ),
            ("text", lambda data: data.__setitem__("title", 1)),
            (
                "review status",
                lambda data: data["sources"][0].__setitem__(
                    "review_status", "approved"
                ),
            ),
            (
                "resource kind",
                lambda data: data["resources"][0].__setitem__(
                    "kind", "worked_example"
                ),
            ),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                data = pack_data()
                mutate(data)
                with self.assertRaises(ValidationError):
                    validate(data)

    def test_schema_v3_rejects_retired_inline_fields(self) -> None:
        cases = (
            lambda data: data["activities"][0].__setitem__("prompt", "Old prompt"),
            lambda data: data["activities"][0].__setitem__(
                "explanation", "Old explanation"
            ),
            lambda data: data["activities"][0]["choices"][1].__setitem__(
                "hint", "Old hint"
            ),
            lambda data: data["activities"][0]["choices"][1].__setitem__(
                "hint_id", "old.hint"
            ),
        )
        for mutate in cases:
            data = pack_data()
            mutate(data)
            with self.assertRaises(ValidationError):
                validate(data)

    def test_ids_text_collections_and_versions_are_bounded(self) -> None:
        cases = (
            lambda data: data.__setitem__("pack_id", " "),
            lambda data: data.__setitem__("title", " "),
            lambda data: data.__setitem__("version", "1.0"),
            lambda data: data["sources"][0].__setitem__("rights", " "),
            lambda data: data["claims"][0]["source_refs"][0].__setitem__(
                "locator", " "
            ),
            lambda data: data.__setitem__("concepts", []),
            lambda data: data.__setitem__("claims", []),
            lambda data: data.__setitem__("resources", []),
            lambda data: data.__setitem__("activities", []),
            lambda data: data["activities"][0].__setitem__("choices", []),
            lambda data: data["resources"][0].__setitem__("claim_ids", []),
        )
        for mutate in cases:
            data = pack_data()
            mutate(data)
            with self.assertRaises(ValidationError):
                validate(data)

    def test_activity_requires_exactly_one_correct_choice(self) -> None:
        for correct_count in (0, 2):
            with self.subTest(correct_count=correct_count):
                data = pack_data()
                first, second = data["activities"][0]["choices"]
                if correct_count == 0:
                    first["correct"] = False
                    first["misconception_id"] = "correct-option-marked-incorrect"
                    first["hint_resource_ids"] = [
                        "observation-vs-intervention.hint.01"
                    ]
                else:
                    second["correct"] = True
                    second.pop("misconception_id")
                    second.pop("hint_resource_ids")

                with self.assertRaises(ValidationError):
                    validate(data)

    def test_scenario_image_paths_are_local_media_pngs(self) -> None:
        data = pack_data()
        data["activities"][0]["scenario_image"] = {
            "path": "media/scenarios/example.png",
            "alt_text": "A neutral scenario image.",
        }
        pack = validate(data)
        assert pack.activities[0].scenario_image is not None
        self.assertEqual(
            pack.activities[0].scenario_image.path, "media/scenarios/example.png"
        )

        for path in ("https://example.test/image.png", "media/../escape.png"):
            with self.subTest(path=path):
                data["activities"][0]["scenario_image"]["path"] = path
                with self.assertRaises(ValidationError):
                    validate(data)

        data["activities"][0]["scenario_image"]["path"] = "media/scenarios/example.png"
        data["activities"][0]["scenario_image"]["unknown"] = "value"
        with self.assertRaises(ValidationError):
            validate(data)

    def test_choice_feedback_shape_is_strict(self) -> None:
        cases = (
            lambda choice: choice.pop("misconception_id"),
            lambda choice: choice.__setitem__("hint_resource_ids", []),
            lambda choice: choice.__setitem__(
                "hint_resource_ids", [choice["hint_resource_ids"][0]] * 2
            ),
        )
        for mutate in cases:
            data = pack_data()
            mutate(data["activities"][0]["choices"][1])
            with self.assertRaises(ValidationError):
                validate(data)

        data = pack_data()
        correct = data["activities"][0]["choices"][0]
        correct["misconception_id"] = "unexpected"
        correct["hint_resource_ids"] = ["observation-vs-intervention.hint.01"]
        with self.assertRaises(ValidationError):
            validate(data)

    def test_claim_requires_exactly_one_provenance_route(self) -> None:
        data = pack_data()
        data["claims"][0]["source_refs"] = []
        with self.assertRaises(ValidationError):
            validate(data)

        data = pack_data()
        data["claims"][0]["deterministic_derivation"] = {
            "method_id": "test.method",
            "method_version": "1.0.0",
        }
        with self.assertRaises(ValidationError):
            validate(data)

        data = pack_data()
        claim = data["claims"][0]
        claim["source_refs"] = []
        claim["deterministic_derivation"] = {
            "method_id": "test.method",
            "method_version": "1.0.0",
        }
        self.assertEqual(
            validate(data).claims[0].deterministic_derivation.method_id,
            "test.method",
        )

        data = pack_data()
        data["claims"][0]["source_refs"] *= 2
        with self.assertRaises(ValidationError):
            validate(data)

    def test_resource_claim_references_are_unique(self) -> None:
        data = pack_data()
        resource = data["resources"][0]
        resource["claim_ids"].append(resource["claim_ids"][0])

        with self.assertRaises(ValidationError):
            validate(data)

    def test_activity_concept_must_resolve(self) -> None:
        data = pack_data()
        data["activities"][0]["concept_id"] = "missing-concept"

        with self.assertRaises(ValidationError):
            validate(data)

    def test_ids_are_unique_within_each_namespace(self) -> None:
        cases = {
            "concept": lambda data: data["concepts"].append(
                copy.deepcopy(data["concepts"][0])
            ),
            "source": lambda data: data["sources"].append(
                copy.deepcopy(data["sources"][0])
            ),
            "claim": lambda data: data["claims"].append(
                copy.deepcopy(data["claims"][0])
            ),
            "resource": lambda data: data["resources"].append(
                copy.deepcopy(data["resources"][0])
            ),
            "activity": lambda data: data["activities"].append(
                copy.deepcopy(data["activities"][0])
            ),
            "option": lambda data: data["activities"][0]["choices"].append(
                copy.deepcopy(data["activities"][0]["choices"][0])
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                data = pack_data()
                mutate(data)
                with self.assertRaises(ValidationError):
                    validate(data)

    def test_option_ids_are_unique_across_activities(self) -> None:
        data = pack_data()
        second_activity = copy.deepcopy(data["activities"][0])
        second_activity["activity_id"] = "observation-vs-intervention.02"
        data["activities"].append(second_activity)

        with self.assertRaises(ValidationError):
            validate(data)

    def test_loader_rejects_duplicate_json_object_keys(self) -> None:
        raw_json = PACK_PATH.read_text(encoding="utf-8")
        cases = (
            raw_json.replace(
                '  "pack_id":',
                '  "pack_id": "duplicate",\n  "pack_id":',
                1,
            ),
            raw_json.replace(
                '      "kind": "question"',
                '      "kind": "hint",\n      "kind": "question"',
                1,
            ),
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "pack.json"
            for duplicate_json in cases:
                path.write_text(duplicate_json, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                    load_content_pack(path)

    def test_ordered_hints_are_preserved(self) -> None:
        data = pack_data()
        second_hint = copy.deepcopy(
            find_by_id(
                data["resources"],
                "resource_id",
                "observation-vs-intervention.hint.01",
            )
        )
        second_hint["resource_id"] = "observation-vs-intervention.hint.02"
        second_hint["text"] = "Now compare conditioning with an explicit intervention."
        data["resources"].append(second_hint)
        authored_order = (
            "observation-vs-intervention.hint.02",
            "observation-vs-intervention.hint.01",
        )
        data["activities"][0]["choices"][1]["hint_resource_ids"] = list(
            authored_order
        )

        pack = validate(data)

        self.assertEqual(pack.activities[0].choices[1].hint_resource_ids, authored_order)
        self.assertTrue(validate_release(pack).releasable)

    def test_committed_schema_is_current(self) -> None:
        from scripts.generate_schema import render_schema

        self.assertEqual(SCHEMA_PATH.read_text(encoding="utf-8"), render_schema())


class ReleaseValidationTest(unittest.TestCase):
    def test_seed_is_releasable_and_uses_every_resource(self) -> None:
        report = validate_release(load_content_pack(PACK_PATH))

        self.assertTrue(report.releasable)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.unused_resource_ids, ())

    def test_missing_activity_resources_fail_closed(self) -> None:
        mutations = (
            (
                "/activities/0/question_resource_id",
                lambda data: data["activities"][0].__setitem__(
                    "question_resource_id", "missing.question"
                ),
            ),
            (
                "/activities/0/explanation_resource_id",
                lambda data: data["activities"][0].__setitem__(
                    "explanation_resource_id", "missing.explanation"
                ),
            ),
            (
                "/activities/0/choices/0/consequence_resource_id",
                lambda data: data["activities"][0]["choices"][0].__setitem__(
                    "consequence_resource_id", "missing.consequence"
                ),
            ),
            (
                "/activities/0/choices/1/hint_resource_ids/0",
                lambda data: data["activities"][0]["choices"][1].__setitem__(
                    "hint_resource_ids", ["missing.hint"]
                ),
            ),
        )
        for path, mutate in mutations:
            data = pack_data()
            mutate(data)
            pack = validate(data)
            with self.assertRaises(ReleaseValidationError) as caught:
                validate_release(pack)
            self.assertEqual(
                release_issues(caught.exception), ((path, "missing-resource"),)
            )

    def test_activity_cannot_use_draft_resource(self) -> None:
        data = pack_data()
        find_by_id(
            data["resources"],
            "resource_id",
            data["activities"][0]["question_resource_id"],
        )["release_status"] = "draft"

        with self.assertRaises(ReleaseValidationError) as caught:
            validate_release(validate(data))

        self.assertEqual(
            release_issues(caught.exception),
            (("/activities/0/question_resource_id", "draft-resource"),),
        )

    def test_resource_kinds_must_match_reference_roles(self) -> None:
        mutations = (
            (
                "/activities/0/question_resource_id",
                lambda data: data["activities"][0].__setitem__(
                    "question_resource_id", "observation-vs-intervention.hint.01"
                ),
            ),
            (
                "/activities/0/explanation_resource_id",
                lambda data: data["activities"][0].__setitem__(
                    "explanation_resource_id",
                    "observation-vs-intervention.question.01",
                ),
            ),
            (
                "/activities/0/choices/0/consequence_resource_id",
                lambda data: data["activities"][0]["choices"][0].__setitem__(
                    "consequence_resource_id",
                    "observation-vs-intervention.question.01",
                ),
            ),
            (
                "/activities/0/choices/1/hint_resource_ids/0",
                lambda data: data["activities"][0]["choices"][1].__setitem__(
                    "hint_resource_ids",
                    ["observation-vs-intervention.explanation.01"],
                ),
            ),
        )
        for path, mutate in mutations:
            data = pack_data()
            mutate(data)
            with self.assertRaises(ReleaseValidationError) as caught:
                validate_release(validate(data))
            self.assertEqual(
                release_issues(caught.exception),
                ((path, "incompatible-resource-kind"),),
            )

    def test_released_resource_requires_existing_released_claim(self) -> None:
        data = pack_data()
        data["resources"][0]["claim_ids"] = ["missing.claim"]
        with self.assertRaises(ReleaseValidationError) as missing:
            validate_release(validate(data))
        self.assertEqual(
            release_issues(missing.exception),
            (("/resources/0/claim_ids/0", "missing-claim"),),
        )

        data = pack_data()
        claim_id = data["resources"][0]["claim_ids"][0]
        find_by_id(data["claims"], "claim_id", claim_id)["release_status"] = "draft"
        with self.assertRaises(ReleaseValidationError) as draft:
            validate_release(validate(data))
        self.assertEqual(
            release_issues(draft.exception),
            (
                ("/resources/0/claim_ids/0", "draft-claim"),
                ("/resources/2/claim_ids/0", "draft-claim"),
                ("/resources/3/claim_ids/0", "draft-claim"),
            ),
        )

    def test_released_claim_requires_existing_reviewed_source(self) -> None:
        data = pack_data()
        data["claims"][0]["source_refs"][0]["source_id"] = "missing.source"
        with self.assertRaises(ReleaseValidationError) as missing:
            validate_release(validate(data))
        self.assertEqual(
            release_issues(missing.exception),
            (("/claims/0/source_refs/0/source_id", "missing-source"),),
        )

        data = pack_data()
        data["sources"][0]["review_status"] = "draft"
        with self.assertRaises(ReleaseValidationError) as draft:
            validate_release(validate(data))
        self.assertEqual(
            release_issues(draft.exception),
            (
                ("/claims/0/source_refs/0/source_id", "unreviewed-source"),
                ("/claims/1/source_refs/0/source_id", "unreviewed-source"),
                ("/claims/2/source_refs/0/source_id", "unreviewed-source"),
            ),
        )

    def test_released_deterministic_claim_does_not_require_source(self) -> None:
        data = pack_data()
        data["sources"] = []
        for index, claim in enumerate(data["claims"]):
            claim["source_refs"] = []
            claim["deterministic_derivation"] = {
                "method_id": f"test.deterministic-rule-{index}",
                "method_version": "1.0.0",
            }

        report = validate_release(validate(data))

        self.assertTrue(report.releasable)

    def test_draft_records_may_keep_unresolved_authoring_references(self) -> None:
        data = pack_data()
        draft_resource = copy.deepcopy(data["resources"][0])
        draft_resource["resource_id"] = "draft.resource"
        draft_resource["claim_ids"] = ["missing.claim"]
        draft_resource["release_status"] = "draft"
        data["resources"].append(draft_resource)

        draft_claim = copy.deepcopy(data["claims"][0])
        draft_claim["claim_id"] = "draft.claim"
        draft_claim["source_refs"][0]["source_id"] = "missing.source"
        draft_claim["release_status"] = "draft"
        data["claims"].append(draft_claim)

        report = validate_release(validate(data))

        self.assertEqual(report.unused_resource_ids, ("draft.resource",))

    def test_unused_released_records_still_fail_closed(self) -> None:
        data = pack_data()
        resource = copy.deepcopy(data["resources"][0])
        resource["resource_id"] = "unused.released"
        resource["claim_ids"] = ["missing.claim"]
        data["resources"].append(resource)

        with self.assertRaises(ReleaseValidationError) as resource_error:
            validate_release(validate(data))

        self.assertEqual(
            release_issues(resource_error.exception),
            (("/resources/5/claim_ids/0", "missing-claim"),),
        )

        data = pack_data()
        claim = copy.deepcopy(data["claims"][0])
        claim["claim_id"] = "unused.released"
        claim["source_refs"][0]["source_id"] = "missing.source"
        data["claims"].append(claim)

        with self.assertRaises(ReleaseValidationError) as claim_error:
            validate_release(validate(data))

        self.assertEqual(
            release_issues(claim_error.exception),
            (("/claims/3/source_refs/0/source_id", "missing-source"),),
        )

    def test_unused_resources_are_reported_in_stable_order(self) -> None:
        data = pack_data()
        template = copy.deepcopy(data["resources"][1])
        first = copy.deepcopy(template)
        first["resource_id"] = "unused.z"
        second = copy.deepcopy(template)
        second["resource_id"] = "unused.a"
        data["resources"].extend((first, second))

        report = validate_release(validate(data))

        self.assertEqual(report.unused_resource_ids, ("unused.a", "unused.z"))

    def test_release_issues_have_stable_path_and_code_order(self) -> None:
        data = pack_data()
        data["sources"][0]["review_status"] = "draft"
        question = find_by_id(
            data["resources"],
            "resource_id",
            data["activities"][0]["question_resource_id"],
        )
        question["release_status"] = "draft"
        question["kind"] = "hint"

        with self.assertRaises(ReleaseValidationError) as caught:
            validate_release(validate(data))

        self.assertEqual(
            release_issues(caught.exception),
            (
                ("/activities/0/question_resource_id", "draft-resource"),
                (
                    "/activities/0/question_resource_id",
                    "incompatible-resource-kind",
                ),
                ("/claims/0/source_refs/0/source_id", "unreviewed-source"),
                ("/claims/1/source_refs/0/source_id", "unreviewed-source"),
                ("/claims/2/source_refs/0/source_id", "unreviewed-source"),
            ),
        )


if __name__ == "__main__":
    unittest.main()
