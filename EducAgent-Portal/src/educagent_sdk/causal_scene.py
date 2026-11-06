"""Pure deterministic transitions for the first authored causal workbench."""

from collections.abc import Iterable
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StringConstraints

from .contracts import (
    CausalScene, CausalSceneEdge, CausalSceneRecord, ContractModel, StableId,
    SemanticVersion, UmbrellaHypothesisId,
)
from .umbrella_simulation import compute_records, hypothesis_edges, simulation_ready


ScenePhase = Literal["hook", "records", "model", "prediction", "comparison", "revision"]
SceneDialogueJob = Literal["orient", "elicit", "interpret", "consolidate"]
PredictionValue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
ReflectionText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=800),
]


class OpenRecords(ContractModel):
    kind: Literal["open_records"] = "open_records"


class SubmitGraph(ContractModel):
    kind: Literal["submit_graph"] = "submit_graph"
    edges: tuple[CausalSceneEdge, ...] = Field(min_length=1)


class SelectHypothesis(ContractModel):
    kind: Literal["select_hypothesis"] = "select_hypothesis"
    hypothesis_id: UmbrellaHypothesisId


class SubmitPrediction(ContractModel):
    kind: Literal["submit_prediction"] = "submit_prediction"
    prediction_id: PredictionValue


class RunIntervention(ContractModel):
    kind: Literal["run_intervention"] = "run_intervention"
    intervention_action_id: StableId


class SubmitRevision(ContractModel):
    kind: Literal["submit_revision"] = "submit_revision"
    edges: tuple[CausalSceneEdge, ...] = Field(min_length=1)
    reflection: ReflectionText | None = None


CausalSceneAction: TypeAlias = Annotated[
    OpenRecords | SubmitGraph | SelectHypothesis | SubmitPrediction | RunIntervention | SubmitRevision,
    Field(discriminator="kind"),
]


class SceneSimulationRun(ContractModel):
    """Frozen unscored comparison; later graph edits cannot rewrite this run."""

    run_id: int = Field(ge=1)
    hypothesis_id: UmbrellaHypothesisId
    prediction_id: PredictionValue
    hypothesis_edges: tuple[CausalSceneEdge, ...]
    hypothesis_result_records: tuple[CausalSceneRecord, ...]
    reference_result_records: tuple[CausalSceneRecord, ...]


class CausalSceneSnapshot(ContractModel):
    """The complete visible object state reconstructed from declared actions."""

    scene_id: StableId
    phase: ScenePhase
    revision: int = Field(ge=0)
    graph_edges: tuple[CausalSceneEdge, ...] = ()
    prediction_id: PredictionValue | None = None
    intervention_action_id: StableId | None = None
    reflection: ReflectionText | None = None
    simulation_version: SemanticVersion | None = None
    minimum_hypotheses: int = Field(default=0, ge=0)
    hypothesis_id: UmbrellaHypothesisId | None = None
    simulation_runs: tuple[SceneSimulationRun, ...] = ()


def initial_scene_snapshot(scene: CausalScene) -> CausalSceneSnapshot:
    """Create the only legal starting state for an authored scene."""

    return CausalSceneSnapshot(
        scene_id=scene.scene_id, phase="hook", revision=0,
        simulation_version=None if scene.simulation is None else scene.simulation.model_version,
        minimum_hypotheses=0 if scene.simulation is None else scene.simulation.minimum_hypotheses,
    )


def apply_scene_action(
    scene: CausalScene,
    snapshot: CausalSceneSnapshot,
    action: CausalSceneAction,
    *,
    input_revision: int,
) -> CausalSceneSnapshot:
    """Validate one learner action and return a new deterministic scene snapshot."""

    if snapshot.scene_id != scene.scene_id:
        raise ValueError("scene snapshot belongs to another scene")
    if input_revision != snapshot.revision:
        raise ValueError("scene action uses a stale revision")

    next_revision = snapshot.revision + 1
    if isinstance(action, OpenRecords):
        _require_phase(snapshot, "hook", action.kind)
        return snapshot.model_copy(update={"phase": "records", "revision": next_revision})
    if isinstance(action, SelectHypothesis):
        if scene.simulation is None or snapshot.phase not in {"records", "model", "prediction", "comparison"}:
            raise ValueError("select_hypothesis is not legal during this scene phase")
        if action.hypothesis_id not in {item.hypothesis_id for item in scene.simulation.hypotheses}:
            raise ValueError("hypothesis is not declared by this scene")
        return snapshot.model_copy(update={
            "phase": "model", "revision": next_revision,
            "hypothesis_id": action.hypothesis_id,
            "graph_edges": hypothesis_edges(action.hypothesis_id),
            "prediction_id": None, "intervention_action_id": None, "reflection": None,
        })
    if isinstance(action, SubmitGraph):
        _require_phase(snapshot, "records", action.kind)
        _validate_graph(scene, action.edges)
        if scene.simulation is not None:
            # Exact catalog membership supplies declared equations, not an
            # inference from arbitrary arrows. Preserve the old graph action.
            selected = next((item.hypothesis_id for item in scene.simulation.hypotheses
                if set((e.parent_id, e.child_id) for e in hypothesis_edges(item.hypothesis_id))
                == set((e.parent_id, e.child_id) for e in action.edges)), None)
            if selected is None:
                raise ValueError("choose a declared hypothesis with explicit mechanisms")
            return apply_scene_action(scene, snapshot, SelectHypothesis(hypothesis_id=selected),
                                      input_revision=input_revision)
        return snapshot.model_copy(
            update={"phase": "model", "revision": next_revision, "graph_edges": action.edges}
        )
    if isinstance(action, SubmitPrediction):
        if not (scene.simulation is not None and snapshot.phase == "comparison"):
            _require_phase(snapshot, "model", action.kind)
        if action.prediction_id not in scene.prediction_ids:
            raise ValueError("prediction is not declared by the causal scene")
        return snapshot.model_copy(
            update={"phase": "prediction", "revision": next_revision,
                    "prediction_id": action.prediction_id, "intervention_action_id": None,
                    "reflection": None}
        )
    if isinstance(action, RunIntervention):
        _require_phase(snapshot, "prediction", action.kind)
        if action.intervention_action_id != scene.intervention.action_id:
            raise ValueError("intervention is not declared by the causal scene")
        runs = snapshot.simulation_runs
        if scene.simulation is not None:
            if snapshot.hypothesis_id is None or snapshot.prediction_id is None:
                raise ValueError("select a hypothesis and commit a prediction before running")
            runs += (SceneSimulationRun(
                run_id=len(runs) + 1, hypothesis_id=snapshot.hypothesis_id,
                prediction_id=snapshot.prediction_id, hypothesis_edges=snapshot.graph_edges,
                hypothesis_result_records=compute_records(scene, snapshot.hypothesis_id, intervene=True),
                reference_result_records=compute_records(scene, scene.simulation.reference_hypothesis_id, intervene=True),
            ),)
        return snapshot.model_copy(
            update={
                "phase": "comparison",
                "revision": next_revision,
                "intervention_action_id": action.intervention_action_id,
                "simulation_runs": runs,
            }
        )
    if snapshot.phase not in {"comparison", "revision"}:
        raise ValueError(
            f"{action.kind} is not legal during the {snapshot.phase} scene phase"
        )
    if not simulation_ready(scene, snapshot):
        raise ValueError("compare at least two declared hypotheses before the final revision")
    if scene.simulation is not None and not action.reflection:
        raise ValueError("record an unscored comparison explanation before the final graph check")
    _validate_graph(scene, action.edges)
    return snapshot.model_copy(
        update={
            "phase": "revision",
            "revision": next_revision,
            "graph_edges": action.edges,
            "reflection": action.reflection,
        }
    )


def replay_scene_actions(
    scene: CausalScene,
    actions: Iterable[tuple[int, CausalSceneAction]],
) -> CausalSceneSnapshot:
    """Replay action/revision pairs without accessing a learner session or provider."""

    snapshot = initial_scene_snapshot(scene)
    for input_revision, action in actions:
        snapshot = apply_scene_action(
            scene, snapshot, action, input_revision=input_revision
        )
    return snapshot


def legal_scene_action_kinds(snapshot: CausalSceneSnapshot) -> tuple[str, ...]:
    """Return the one declared learner action available in the current phase."""

    if snapshot.simulation_version is not None:
        if snapshot.phase == "records":
            return ("select_hypothesis", "submit_graph")
        if snapshot.phase == "model":
            return ("select_hypothesis", "submit_prediction")
        if snapshot.phase == "prediction":
            return ("select_hypothesis", "run_intervention")
        if snapshot.phase == "comparison":
            ready = len({run.hypothesis_id for run in snapshot.simulation_runs}) >= snapshot.minimum_hypotheses
            return ("select_hypothesis", "submit_prediction") + (("submit_revision",) if ready else ())
    return {
        "hook": ("open_records",),
        "records": ("submit_graph",),
        "model": ("submit_prediction",),
        "prediction": ("run_intervention",),
        "comparison": ("submit_revision",),
        "revision": ("submit_revision",),
    }[snapshot.phase]


def legal_scene_focus_ids(snapshot: CausalSceneSnapshot) -> tuple[StableId, ...]:
    """Return the sole typed pedagogical focus licensed by the scene phase."""

    return {
        "hook": ("scene.open-records",),
        "records": ("scene.propose-model",),
        "model": ("scene.elicit-prediction",),
        "prediction": ("scene.run-intervention",),
        "comparison": ("scene.interpret-result",),
        "revision": ("scene.formal-evidence",),
    }[snapshot.phase]


def dialogue_job_for_scene_focus(focus_id: StableId) -> SceneDialogueJob:
    """Derive the visible Socratic job from one declared interaction focus."""

    return {
        "scene.open-records": "orient",
        "scene.propose-model": "elicit",
        "scene.elicit-prediction": "elicit",
        "scene.run-intervention": "orient",
        "scene.interpret-result": "interpret",
        "scene.formal-evidence": "consolidate",
    }[focus_id]


def scene_text_projection(
    scene: CausalScene,
    snapshot: CausalSceneSnapshot,
) -> str:
    """Provide the non-visual equivalent of the current causal object state."""

    graph = (
        "No proposed arrows have been submitted."
        if not snapshot.graph_edges
        else "; ".join(
            f"{_node_label(scene, edge.parent_id)} points to {_node_label(scene, edge.child_id)}"
            for edge in snapshot.graph_edges
        )
    )
    records = "Observational records are not yet open."
    if snapshot.phase != "hook":
        records = _records_text("Observed records", scene.observed_records)
    intervention = "No intervention result has been revealed."
    if snapshot.intervention_action_id is not None:
        result_records = (snapshot.simulation_runs[-1].reference_result_records
                          if scene.simulation is not None else scene.intervention.result_records)
        intervention = _records_text(
            "Reference-world intervention result" if scene.simulation else "Intervention result", result_records
        )
        before_total = sum(row.arrivals for row in scene.observed_records)
        after_total = sum(row.arrivals for row in result_records)
        intervention += (
            f" Population comparison: {before_total} arrival records before; "
            f"{after_total} after. All records remain, rather than selecting a subgroup."
        )
        if scene.intervention.variable_id == "umbrella-carried":
            filtered_total = sum(
                row.arrivals for row in scene.observed_records
                if row.umbrella_carried == scene.intervention.value
            )
            intervention += (
                " Filtering the original records to umbrella carried "
                f"{scene.intervention.value} would retain {filtered_total} arrival records, "
                f"not the {after_total} records in this intervention result."
            )
        if scene.simulation is not None:
            run = snapshot.simulation_runs[-1]
            hypothesis = next(item for item in scene.simulation.hypotheses if item.hypothesis_id == run.hypothesis_id)
            intervention += " " + _records_text("Student hypothesis simulation (not the reference world)", run.hypothesis_result_records)
            intervention += f" This run uses the declared hypothesis: {hypothesis.label}. Mechanism: {hypothesis.mechanism}."
            intervention += f" Tried {len({item.hypothesis_id for item in snapshot.simulation_runs})} distinct hypotheses; {scene.simulation.minimum_hypotheses} required before the reference-model revision."
            if simulation_ready(scene, snapshot):
                reference = next(item for item in scene.simulation.hypotheses if item.hypothesis_id == scene.simulation.reference_hypothesis_id)
                intervention += f" Disclosed reference assumptions: {reference.mechanism}. Matching one intervention does not identify a unique graph."
    prediction = (
        "No prediction has been recorded."
        if snapshot.prediction_id is None
        else f"Prediction recorded: {snapshot.prediction_id}."
    )
    return " ".join(
        (
            f"Scene phase: {snapshot.phase}. Scene version: {snapshot.revision}.",
            records,
            f"Current model: {graph}.",
            prediction,
            intervention,
        )
    )


def _validate_graph(scene: CausalScene, edges: tuple[CausalSceneEdge, ...]) -> None:
    allowed = {(edge.parent_id, edge.child_id) for edge in scene.permitted_edges}
    proposed = tuple((edge.parent_id, edge.child_id) for edge in edges)
    if len(proposed) != len(set(proposed)):
        raise ValueError("scene graph contains duplicate edges")
    if not set(proposed).issubset(allowed):
        raise ValueError("scene graph contains an undeclared edge")
    children: dict[str, set[str]] = {}
    for parent, child in proposed:
        children.setdefault(parent, set()).add(child)
    visited: set[str] = set()
    active: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            raise ValueError("scene graph must be acyclic")
        if node in visited:
            return
        active.add(node)
        for child in children.get(node, ()):
            visit(child)
        active.remove(node)
        visited.add(node)

    for node in children:
        visit(node)


def _require_phase(
    snapshot: CausalSceneSnapshot, expected: ScenePhase, action_kind: str
) -> None:
    if snapshot.phase != expected:
        raise ValueError(
            f"{action_kind} is not legal during the {snapshot.phase} scene phase"
        )


def _node_label(scene: CausalScene, node_id: str) -> str:
    return next(node.label for node in scene.nodes if node.node_id == node_id)


def _records_text(label: str, records: Iterable[object]) -> str:
    rows = tuple(records)
    return f"{label}: {sum(row.arrivals for row in rows)} arrival records total; " + "; ".join(
        f"umbrella carried {row.umbrella_carried}, pavement wet {row.pavement_wet}, {row.arrivals} arrival records"
        for row in rows
    )
