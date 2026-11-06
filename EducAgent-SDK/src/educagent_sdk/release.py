"""Release validation for structurally valid content packs."""

from .contracts import (
    ContentPack,
    ContractModel,
    NonEmptyText,
    ResourceKind,
    StableId,
)


class ReleaseIssue(ContractModel):
    """One release blocker located by JSON Pointer in the authored pack."""

    code: StableId
    path: NonEmptyText
    message: NonEmptyText


class ReleaseReport(ContractModel):
    """Release result plus non-blocking unused-resource findings."""

    issues: tuple[ReleaseIssue, ...] = ()
    unused_resource_ids: tuple[StableId, ...] = ()

    @property
    def releasable(self) -> bool:
        return not self.issues


class ReleaseValidationError(ValueError):
    """Raised when a structurally valid pack is not releasable."""

    def __init__(self, report: ReleaseReport) -> None:
        self.report = report
        details = "; ".join(
            f"{issue.path}: {issue.message}" for issue in report.issues
        )
        super().__init__(f"content pack is not releasable: {details}")


def validate_release(pack: ContentPack) -> ReleaseReport:
    """Validate released records and all activity-used resources in one pass."""

    sources = {source.source_id: source for source in pack.sources}
    claims = {claim.claim_id: claim for claim in pack.claims}
    resources = {resource.resource_id: resource for resource in pack.resources}
    issues: list[ReleaseIssue] = []
    used_resource_ids: set[str] = set()

    def require_resource(resource_id: str, kind: ResourceKind, path: str) -> None:
        used_resource_ids.add(resource_id)
        resource = resources.get(resource_id)
        if resource is None:
            issues.append(
                ReleaseIssue(
                    code="missing-resource",
                    path=path,
                    message=f"resource does not exist: {resource_id}",
                )
            )
            return
        if resource.release_status != "released":
            issues.append(
                ReleaseIssue(
                    code="draft-resource",
                    path=path,
                    message=f"resource is not released: {resource_id}",
                )
            )
        if resource.kind != kind:
            issues.append(
                ReleaseIssue(
                    code="incompatible-resource-kind",
                    path=path,
                    message=(
                        f"expected {kind} resource, got {resource.kind}: {resource_id}"
                    ),
                )
            )

    for activity_index, activity in enumerate(pack.activities):
        activity_path = f"/activities/{activity_index}"
        require_resource(
            activity.question_resource_id,
            "question",
            f"{activity_path}/question_resource_id",
        )
        require_resource(
            activity.explanation_resource_id,
            "explanation",
            f"{activity_path}/explanation_resource_id",
        )
        if activity.experiment is not None:
            require_resource(
                activity.experiment.instructions_resource_id, "explanation",
                f"{activity_path}/experiment/instructions_resource_id",
            )
        if activity.workbench is not None:
            question = resources.get(activity.question_resource_id)
            if question is not None:
                visible_text = " ".join(question.text.casefold().split())
                if activity.workbench.prompt is not None and (
                    " ".join(activity.workbench.prompt.casefold().split()) not in visible_text
                ):
                    issues.append(ReleaseIssue(
                        code="ungrounded-workbench",
                        path=f"{activity_path}/workbench/prompt",
                        message="comparison prompt must occur in the released current question",
                    ))
                # Tables may reorganise released observations, not introduce
                # another factual source or a future result beside the question.
                for table_index, table in enumerate(activity.workbench.tables):
                    observations = (*table.columns, *(cell for row in table.rows for cell in row))
                    if any(" ".join(cell.casefold().split()) not in visible_text for cell in observations):
                        issues.append(ReleaseIssue(
                            code="ungrounded-workbench",
                            path=f"{activity_path}/workbench/tables/{table_index}",
                            message="comparison columns and cells must occur in the released current question",
                        ))
        for choice_index, choice in enumerate(activity.choices):
            choice_path = f"{activity_path}/choices/{choice_index}"
            require_resource(
                choice.consequence_resource_id,
                "consequence",
                f"{choice_path}/consequence_resource_id",
            )
            for index, hint_resource_id in enumerate(choice.hint_resource_ids):
                require_resource(
                    hint_resource_id,
                    "hint",
                    f"{choice_path}/hint_resource_ids/{index}",
                )

    for scene_index, scene in enumerate(pack.causal_scenes):
        scene_path = f"/causal_scenes/{scene_index}"
        for field_name, resource_id, kind in (
            ("hook_resource_id", scene.hook_resource_id, "question"),
            ("records_resource_id", scene.records_resource_id, "explanation"),
            ("model_resource_id", scene.model_resource_id, "explanation"),
            ("prediction_resource_id", scene.prediction_resource_id, "question"),
            ("intervention_resource_id", scene.intervention_resource_id, "question"),
            ("result_resource_id", scene.result_resource_id, "consequence"),
            ("reflection_resource_id", scene.reflection_resource_id, "question"),
            (
                "direct_explanation_resource_id",
                scene.direct_explanation_resource_id,
                "explanation",
            ),
        ):
            require_resource(resource_id, kind, f"{scene_path}/{field_name}")
        for claim_id in scene.claim_ids:
            claim = claims.get(claim_id)
            if claim is None:
                issues.append(
                    ReleaseIssue(
                        code="missing-claim",
                        path=f"{scene_path}/claim_ids",
                        message=f"claim does not exist: {claim_id}",
                    )
                )
            elif claim.release_status != "released":
                issues.append(
                    ReleaseIssue(
                        code="draft-claim",
                        path=f"{scene_path}/claim_ids",
                        message=f"claim is not released: {claim_id}",
                    )
                )
        require_resource(
            scene.assessment.accepted_consequence_resource_id,
            "consequence",
            f"{scene_path}/assessment/accepted_consequence_resource_id",
        )
        require_resource(
            scene.assessment.rejected_consequence_resource_id,
            "consequence",
            f"{scene_path}/assessment/rejected_consequence_resource_id",
        )
        for hint_index, resource_id in enumerate(scene.assessment.hint_resource_ids):
            require_resource(
                resource_id,
                "hint",
                f"{scene_path}/assessment/hint_resource_ids/{hint_index}",
            )

    if pack.lesson is not None:
        for field_path, resource_id, kind in pack.lesson.resource_references():
            require_resource(resource_id, kind, "/lesson/" + field_path)
    for index, lesson in enumerate(pack.lessons):
        for field_path, resource_id, kind in lesson.resource_references():
            require_resource(resource_id, kind, f"/lessons/{index}/" + field_path)

    for resource_index, resource in enumerate(pack.resources):
        if resource.release_status != "released":
            continue
        for index, claim_id in enumerate(resource.claim_ids):
            path = f"/resources/{resource_index}/claim_ids/{index}"
            claim = claims.get(claim_id)
            if claim is None:
                issues.append(
                    ReleaseIssue(
                        code="missing-claim",
                        path=path,
                        message=f"claim does not exist: {claim_id}",
                    )
                )
            elif claim.release_status != "released":
                issues.append(
                    ReleaseIssue(
                        code="draft-claim",
                        path=path,
                        message=f"claim is not released: {claim_id}",
                    )
                )

    for claim_index, claim in enumerate(pack.claims):
        if claim.release_status != "released":
            continue
        for index, source_ref in enumerate(claim.source_refs):
            path = f"/claims/{claim_index}/source_refs/{index}/source_id"
            source = sources.get(source_ref.source_id)
            if source is None:
                issues.append(
                    ReleaseIssue(
                        code="missing-source",
                        path=path,
                        message=f"source does not exist: {source_ref.source_id}",
                    )
                )
            elif source.review_status != "reviewed":
                issues.append(
                    ReleaseIssue(
                        code="unreviewed-source",
                        path=path,
                        message=f"source is not reviewed: {source_ref.source_id}",
                    )
                )

    report = ReleaseReport(
        issues=tuple(sorted(issues, key=lambda issue: (issue.path, issue.code))),
        unused_resource_ids=tuple(sorted(set(resources) - used_resource_ids)),
    )
    if report.issues:
        raise ReleaseValidationError(report)
    return report
