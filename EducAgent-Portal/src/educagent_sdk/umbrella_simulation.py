"""Finite umbrella hypotheses evaluated independently of the reference world.

The catalog version fixes the Boolean equations. Authors supply labels and a
finite root distribution; arbitrary learner arrows never imply new equations.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from .contracts import CausalScene, CausalSceneEdge, CausalSceneRecord, UmbrellaHypothesisId
from .causal_world import BinaryCausalWorld, CausalEdge, StructuralEquation, evaluate_world

if TYPE_CHECKING:
    from .causal_scene import CausalSceneSnapshot


def hypothesis_world(hypothesis_id: UmbrellaHypothesisId) -> BinaryCausalWorld:
    """Return the declared version-1 mechanism, including its exogenous root."""

    umbrella, wet = "umbrella-carried", "pavement-wet"
    if hypothesis_id == "rain-common-cause":
        root, children = "rain", (umbrella, wet)
    elif hypothesis_id == "umbrella-causes-wet":
        root, children = umbrella, (wet,)
    elif hypothesis_id == "wet-causes-umbrella":
        root, children = wet, (umbrella,)
    else:
        raise ValueError("unknown umbrella hypothesis")
    return BinaryCausalWorld(
        world_id=f"umbrella.{hypothesis_id}.v1", node_ids=(root, *children),
        exogenous_node_ids=(root,),
        edges=tuple(CausalEdge(parent_id=root, child_id=child) for child in children),
        equations=tuple(StructuralEquation(node_id=child, parent_ids=(root,), operator="copy")
                        for child in children),
    )


def hypothesis_edges(hypothesis_id: UmbrellaHypothesisId) -> tuple[CausalSceneEdge, ...]:
    return tuple(CausalSceneEdge(parent_id=edge.parent_id, child_id=edge.child_id)
                 for edge in hypothesis_world(hypothesis_id).edges)


def compute_records(scene: CausalScene, hypothesis_id: UmbrellaHypothesisId,
                    *, intervene: bool) -> tuple[CausalSceneRecord, ...]:
    """Aggregate the same weighted contexts, replacing U's equation under do."""

    config = scene.simulation
    if config is None or hypothesis_id not in {item.hypothesis_id for item in config.hypotheses}:
        raise ValueError("hypothesis is not declared by this scene")
    world = hypothesis_world(hypothesis_id)
    root = world.exogenous_node_ids[0]
    intervention = {scene.intervention.variable_id: scene.intervention.value == "yes"} if intervene else {}
    counts: Counter[tuple[str, str]] = Counter()
    for root_value, weight in ((True, config.root_yes_count),
                               (False, config.population_size - config.root_yes_count)):
        # do(root=...) replaces that root's generating context too, rather than
        # filtering the original population down to matching observations.
        context = {} if root in intervention else {root: root_value}
        values = evaluate_world(world, exogenous_values=context, interventions=intervention)
        key = ("yes" if values["umbrella-carried"] else "no",
               "yes" if values["pavement-wet"] else "no")
        counts[key] += weight
    return tuple(CausalSceneRecord(umbrella_carried=u, pavement_wet=w, arrivals=counts[(u, w)])
                 for u in ("yes", "no") for w in ("yes", "no"))


def _record_counts(records) -> Counter:
    counts: Counter = Counter()
    for row in records:
        counts[(row.umbrella_carried, row.pavement_wet)] += row.arrivals
    return +counts


def validate_scene_simulation(scene: CausalScene) -> None:
    """Reject authored mechanism/data mismatches before any learner session."""

    config = scene.simulation
    assert config is not None
    if scene.intervention.variable_id != "umbrella-carried" or scene.intervention.value != "yes":
        raise ValueError("umbrella simulation v1 requires the declared do(U=yes) intervention")
    if config.population_size != sum(row.arrivals for row in scene.observed_records):
        raise ValueError("scene simulation population must match observed records")
    permitted = {(edge.parent_id, edge.child_id) for edge in scene.permitted_edges}
    nodes = {node.node_id for node in scene.nodes}
    for hypothesis in config.hypotheses:
        world = hypothesis_world(hypothesis.hypothesis_id)
        if not set(world.node_ids).issubset(nodes) or not {
            (edge.parent_id, edge.child_id) for edge in world.edges
        }.issubset(permitted):
            raise ValueError("scene hypothesis uses undeclared nodes or arrows")
        if _record_counts(compute_records(scene, hypothesis.hypothesis_id, intervene=False)) != _record_counts(scene.observed_records):
            raise ValueError("scene hypothesis does not reproduce its declared observations")
    if _record_counts(compute_records(scene, config.reference_hypothesis_id, intervene=True)) != _record_counts(scene.intervention.result_records):
        raise ValueError("computed reference world does not match the versioned scene result")
    if {(e.parent_id, e.child_id) for e in hypothesis_edges(config.reference_hypothesis_id)} != {
        (e.parent_id, e.child_id) for e in scene.assessment.accepted_edges
    }:
        raise ValueError("final scene rubric must represent the declared reference assumptions")


def simulation_ready(scene: CausalScene, snapshot: CausalSceneSnapshot) -> bool:
    return scene.simulation is None or len({run.hypothesis_id for run in snapshot.simulation_runs}) >= scene.simulation.minimum_hypotheses


def public_simulation_view(scene: CausalScene, snapshot: CausalSceneSnapshot) -> dict | None:
    """Only declared learner mechanisms and executed results cross this boundary."""

    config = scene.simulation
    if config is None:
        return None
    ready = simulation_ready(scene, snapshot)
    hypotheses = {item.hypothesis_id: item for item in config.hypotheses}
    public_hypotheses = []
    if snapshot.phase != "hook":
        labels = {node.node_id: node.label for node in scene.nodes}
        for hypothesis in config.hypotheses:
            world = hypothesis_world(hypothesis.hypothesis_id)
            root_id = world.exogenous_node_ids[0]
            public_hypotheses.append({
                **hypothesis.model_dump(),
                "root_variable_id": root_id, "root_variable_label": labels[root_id],
                "active_node_ids": list(world.node_ids),
                "edges": [edge.model_dump() for edge in world.edges],
            })

    def wet_pct(records) -> float:
        return 100 * sum(row.arrivals for row in records if row.pavement_wet == "yes") / config.population_size

    return {
        "kind": config.kind, "model_version": config.model_version,
        "hypotheses": public_hypotheses,
        "selected_hypothesis_id": snapshot.hypothesis_id,
        "runs": [{
            "run_id": run.run_id, "hypothesis_id": run.hypothesis_id,
            "hypothesis_label": hypotheses[run.hypothesis_id].label,
            "prediction_id": run.prediction_id,
            "hypothesis_edges": [edge.model_dump() for edge in run.hypothesis_edges],
            "hypothesis_result_records": [row.model_dump() for row in run.hypothesis_result_records],
            "reference_result_records": [row.model_dump() for row in run.reference_result_records],
            "hypothesis_wet_pct": wet_pct(run.hypothesis_result_records),
            "reference_wet_pct": wet_pct(run.reference_result_records),
        } for run in snapshot.simulation_runs],
        "minimum_hypotheses": config.minimum_hypotheses,
        "distinct_hypotheses_tried": len({run.hypothesis_id for run in snapshot.simulation_runs}),
        "ready_for_revision": ready,
        "reference_assumptions": hypotheses[config.reference_hypothesis_id].mechanism if ready else None,
        "reference_edges": [edge.model_dump() for edge in hypothesis_edges(config.reference_hypothesis_id)] if ready else None,
    }
