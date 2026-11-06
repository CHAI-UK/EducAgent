"""Small deterministic binary structural-causal worlds for Causality M1."""

from collections.abc import Iterable
from itertools import product
from typing import Literal, Self

from pydantic import Field, model_validator

from .contracts import ContractModel, StableId


EquationOperator = Literal["constant", "copy", "not", "and", "or", "xor"]
DagMatch = Literal["matches", "missing_edges", "extra_edges", "reversed_edges", "mixed"]
ReasoningMatch = Literal["correct", "incorrect_intervention_result"]


class CausalEdge(ContractModel):
    parent_id: StableId
    child_id: StableId

    @model_validator(mode="after")
    def validate_distinct_nodes(self) -> Self:
        if self.parent_id == self.child_id:
            raise ValueError("a causal edge cannot connect a node to itself")
        return self


class StructuralEquation(ContractModel):
    """A deliberately small Boolean structural equation."""

    node_id: StableId
    parent_ids: tuple[StableId, ...] = ()
    operator: EquationOperator
    constant: bool | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        arity = len(self.parent_ids)
        if len(set(self.parent_ids)) != arity:
            raise ValueError("equation parent IDs must be unique")
        if self.operator == "constant":
            if arity or self.constant is None:
                raise ValueError("a constant equation needs one constant and no parents")
        elif self.constant is not None:
            raise ValueError("only a constant equation may define constant")
        elif self.operator in {"copy", "not"} and arity != 1:
            raise ValueError(f"{self.operator} needs exactly one parent")
        elif self.operator in {"and", "or", "xor"} and arity != 2:
            raise ValueError(f"{self.operator} needs exactly two parents")
        return self


class BinaryCausalWorld(ContractModel):
    """A finite acyclic SCM with explicit graph and equation provenance."""

    world_id: StableId
    node_ids: tuple[StableId, ...] = Field(min_length=1)
    exogenous_node_ids: tuple[StableId, ...] = ()
    edges: tuple[CausalEdge, ...] = ()
    equations: tuple[StructuralEquation, ...] = ()

    @model_validator(mode="after")
    def validate_world(self) -> Self:
        nodes = set(self.node_ids)
        if len(nodes) != len(self.node_ids):
            raise ValueError("world node IDs must be unique")
        if not set(self.exogenous_node_ids).issubset(nodes):
            raise ValueError("exogenous nodes must belong to the world")
        if len(set(self.exogenous_node_ids)) != len(self.exogenous_node_ids):
            raise ValueError("exogenous node IDs must be unique")
        equation_by_node = {equation.node_id: equation for equation in self.equations}
        if len(equation_by_node) != len(self.equations):
            raise ValueError("world equations must have unique node IDs")
        if set(equation_by_node) != nodes - set(self.exogenous_node_ids):
            raise ValueError("every non-exogenous node needs exactly one equation")
        expected_edges = {
            (parent_id, equation.node_id)
            for equation in self.equations
            for parent_id in equation.parent_ids
        }
        edge_pairs = {(edge.parent_id, edge.child_id) for edge in self.edges}
        if len(edge_pairs) != len(self.edges):
            raise ValueError("world edges must be unique")
        if any(parent not in nodes or child not in nodes for parent, child in edge_pairs):
            raise ValueError("world edges must use declared nodes")
        if edge_pairs != expected_edges:
            raise ValueError("world edges must exactly match equation parents")
        _topological_nodes(self.node_ids, edge_pairs)
        return self


class LearnerDagSubmission(ContractModel):
    """A learner-authored DAG with immutable activity/artifact provenance."""

    artifact_id: StableId
    activity_id: StableId
    world_id: StableId
    node_ids: tuple[StableId, ...]
    edges: tuple[CausalEdge, ...]

    @model_validator(mode="after")
    def validate_submission(self) -> Self:
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("learner DAG node IDs must be unique")
        pairs = {(edge.parent_id, edge.child_id) for edge in self.edges}
        if len(pairs) != len(self.edges):
            raise ValueError("learner DAG edges must be unique")
        if any(
            edge.parent_id not in self.node_ids or edge.child_id not in self.node_ids
            for edge in self.edges
        ):
            raise ValueError("learner DAG edges must use its declared nodes")
        _topological_nodes(self.node_ids, pairs)
        return self


class CausalDiagnosis(ContractModel):
    """Separate structural-model error from intervention-reasoning error."""

    world_id: StableId
    artifact_id: StableId
    model_match: DagMatch
    missing_edges: tuple[CausalEdge, ...] = ()
    extra_edges: tuple[CausalEdge, ...] = ()
    reversed_edges: tuple[CausalEdge, ...] = ()
    reasoning_match: ReasoningMatch
    expected_outcome: bool
    learner_outcome: bool


class BinaryRecord(ContractModel):
    """One fully observed binary row for a deterministic adjusted estimate."""

    values: dict[StableId, bool] = Field(min_length=1)


def evaluate_world(
    world: BinaryCausalWorld,
    *,
    exogenous_values: dict[StableId, bool],
    interventions: dict[StableId, bool] | None = None,
) -> dict[StableId, bool]:
    """Evaluate one context under optional ``do`` interventions."""

    interventions = interventions or {}
    nodes = set(world.node_ids)
    if not set(exogenous_values).issubset(set(world.exogenous_node_ids)):
        raise ValueError("exogenous values may name only exogenous nodes")
    if not set(interventions).issubset(nodes):
        raise ValueError("interventions must name declared world nodes")
    required_exogenous = set(world.exogenous_node_ids) - set(interventions)
    if set(exogenous_values) != required_exogenous:
        raise ValueError("provide exactly the non-intervened exogenous values")
    if any(type(value) is not bool for value in (*exogenous_values.values(), *interventions.values())):
        raise TypeError("binary world values must be booleans")

    equations = {equation.node_id: equation for equation in world.equations}
    values: dict[StableId, bool] = {}
    for node_id in _topological_nodes(
        world.node_ids, {(edge.parent_id, edge.child_id) for edge in world.edges}
    ):
        if node_id in interventions:
            values[node_id] = interventions[node_id]
        elif node_id in world.exogenous_node_ids:
            values[node_id] = exogenous_values[node_id]
        else:
            equation = equations[node_id]
            values[node_id] = _apply_equation(equation, values)
    return values


def diagnose_intervention_answer(
    world: BinaryCausalWorld,
    submission: LearnerDagSubmission,
    *,
    exogenous_values: dict[StableId, bool],
    interventions: dict[StableId, bool],
    outcome_id: StableId,
    learner_outcome: bool,
) -> CausalDiagnosis:
    """Diagnose a submitted DAG and an intervention answer independently."""

    if submission.world_id != world.world_id:
        raise ValueError("learner DAG was submitted for another causal world")
    if tuple(submission.node_ids) != tuple(world.node_ids):
        raise ValueError("learner DAG must use the world's declared node ordering")
    if outcome_id not in world.node_ids or type(learner_outcome) is not bool:
        raise ValueError("outcome ID and learner outcome must be valid")
    expected = evaluate_world(
        world, exogenous_values=exogenous_values, interventions=interventions
    )[outcome_id]
    expected_edges = {(edge.parent_id, edge.child_id) for edge in world.edges}
    actual_edges = {(edge.parent_id, edge.child_id) for edge in submission.edges}
    missing = expected_edges - actual_edges
    extra = actual_edges - expected_edges
    reversed_pairs = {
        pair for pair in missing if (pair[1], pair[0]) in actual_edges
    }
    missing -= reversed_pairs
    extra -= {(child, parent) for parent, child in reversed_pairs}
    model_match = _dag_match(missing, extra, reversed_pairs)
    return CausalDiagnosis(
        world_id=world.world_id,
        artifact_id=submission.artifact_id,
        model_match=model_match,
        missing_edges=_edges(missing),
        extra_edges=_edges(extra),
        reversed_edges=_edges(reversed_pairs),
        reasoning_match=(
            "correct" if learner_outcome == expected else "incorrect_intervention_result"
        ),
        expected_outcome=expected,
        learner_outcome=learner_outcome,
    )


def evaluate_counterfactual(
    world: BinaryCausalWorld,
    *,
    abducted_exogenous_values: dict[StableId, bool],
    interventions: dict[StableId, bool],
) -> dict[StableId, bool]:
    """Evaluate a deterministic counterfactual after exogenous context is fixed.

    In this compact SCM, abduction is supplied explicitly as the already-fixed
    exogenous context. Later worlds may add a separate probabilistic abduction
    mechanism without changing the generic learning runtime.
    """

    return evaluate_world(
        world,
        exogenous_values=abducted_exogenous_values,
        interventions=interventions,
    )


def is_valid_backdoor_adjustment_set(
    world: BinaryCausalWorld,
    *,
    treatment_id: StableId,
    outcome_id: StableId,
    adjustment_node_ids: Iterable[StableId],
) -> bool:
    """Check the backdoor criterion by d-separation in the mutilated DAG."""

    adjustment = tuple(adjustment_node_ids)
    nodes = set(world.node_ids)
    if treatment_id not in nodes or outcome_id not in nodes:
        raise ValueError("treatment and outcome must be world nodes")
    if len(set(adjustment)) != len(adjustment) or not set(adjustment).issubset(nodes):
        raise ValueError("adjustment nodes must be unique declared nodes")
    if treatment_id in adjustment or outcome_id in adjustment:
        return False
    if set(adjustment) & _descendants(world, treatment_id):
        return False
    edges = {
        (edge.parent_id, edge.child_id)
        for edge in world.edges
        if edge.parent_id != treatment_id
    }
    return _d_separated(world.node_ids, edges, treatment_id, outcome_id, set(adjustment))


def estimate_adjusted_risk(
    records: Iterable[BinaryRecord],
    *,
    treatment_id: StableId,
    outcome_id: StableId,
    treatment_value: bool,
    adjustment_node_ids: Iterable[StableId] = (),
) -> float:
    """Estimate a binary intervention risk by deterministic standardization."""

    rows = tuple(records)
    adjustment = tuple(adjustment_node_ids)
    required = {treatment_id, outcome_id, *adjustment}
    if not rows or any(not required.issubset(row.values) for row in rows):
        raise ValueError("every record must contain treatment, outcome, and adjustment nodes")
    total = len(rows)
    estimate = 0.0
    for values in product((False, True), repeat=len(adjustment)):
        stratum = dict(zip(adjustment, values, strict=True))
        in_stratum = [
            row for row in rows if all(row.values[node] == value for node, value in stratum.items())
        ]
        treated = [
            row for row in in_stratum if row.values[treatment_id] == treatment_value
        ]
        if not in_stratum or not treated:
            raise ValueError("records do not identify every required adjustment stratum")
        estimate += (len(in_stratum) / total) * (
            sum(row.values[outcome_id] for row in treated) / len(treated)
        )
    return estimate


def _topological_nodes(
    node_ids: Iterable[StableId], edges: set[tuple[StableId, StableId]]
) -> tuple[StableId, ...]:
    remaining = set(node_ids)
    result: list[StableId] = []
    while remaining:
        ready = sorted(
            node
            for node in remaining
            if not any(
                child == node and parent in remaining for parent, child in edges
            )
        )
        if not ready:
            raise ValueError("causal graph must be acyclic")
        result.extend(ready)
        remaining.difference_update(ready)
    return tuple(result)


def _apply_equation(
    equation: StructuralEquation, values: dict[StableId, bool]
) -> bool:
    inputs = tuple(values[parent] for parent in equation.parent_ids)
    if equation.operator == "constant":
        assert equation.constant is not None
        return equation.constant
    if equation.operator == "copy":
        return inputs[0]
    if equation.operator == "not":
        return not inputs[0]
    if equation.operator == "and":
        return inputs[0] and inputs[1]
    if equation.operator == "or":
        return inputs[0] or inputs[1]
    return inputs[0] != inputs[1]


def _descendants(world: BinaryCausalWorld, node_id: StableId) -> set[StableId]:
    children: dict[StableId, set[StableId]] = {node: set() for node in world.node_ids}
    for edge in world.edges:
        children[edge.parent_id].add(edge.child_id)
    result: set[StableId] = set()
    frontier = list(children[node_id])
    while frontier:
        current = frontier.pop()
        if current not in result:
            result.add(current)
            frontier.extend(children[current])
    return result


def _d_separated(
    node_ids: Iterable[StableId],
    edges: set[tuple[StableId, StableId]],
    start: StableId,
    end: StableId,
    conditioned: set[StableId],
) -> bool:
    neighbors: dict[StableId, set[StableId]] = {node: set() for node in node_ids}
    for parent, child in edges:
        neighbors[parent].add(child)
        neighbors[child].add(parent)
    for path in _simple_paths(neighbors, start, end):
        if not _path_is_blocked(path, edges, conditioned):
            return False
    return True


def _simple_paths(
    neighbors: dict[StableId, set[StableId]], start: StableId, end: StableId
) -> Iterable[tuple[StableId, ...]]:
    frontier = [(start, (start,))]
    while frontier:
        node, path = frontier.pop()
        if node == end:
            yield path
            continue
        frontier.extend(
            (neighbor, (*path, neighbor))
            for neighbor in neighbors[node] - set(path)
        )


def _path_is_blocked(
    path: tuple[StableId, ...],
    edges: set[tuple[StableId, StableId]],
    conditioned: set[StableId],
) -> bool:
    descendants = _edge_descendants(edges)
    for index in range(1, len(path) - 1):
        previous, node, following = path[index - 1], path[index], path[index + 1]
        collider = (previous, node) in edges and (following, node) in edges
        if collider:
            if node not in conditioned and not (
                descendants.get(node, set()) & conditioned
            ):
                return True
        elif node in conditioned:
            return True
    return False


def _edge_descendants(
    edges: set[tuple[StableId, StableId]],
) -> dict[StableId, set[StableId]]:
    children: dict[StableId, set[StableId]] = {}
    for parent, child in edges:
        children.setdefault(parent, set()).add(child)
        children.setdefault(child, set())
    result: dict[StableId, set[StableId]] = {}
    for node in children:
        found: set[StableId] = set()
        frontier = list(children[node])
        while frontier:
            current = frontier.pop()
            if current not in found:
                found.add(current)
                frontier.extend(children[current])
        result[node] = found
    return result


def _dag_match(
    missing: set[tuple[StableId, StableId]],
    extra: set[tuple[StableId, StableId]],
    reversed_pairs: set[tuple[StableId, StableId]],
) -> DagMatch:
    kinds = sum(bool(group) for group in (missing, extra, reversed_pairs))
    if not kinds:
        return "matches"
    if kinds > 1:
        return "mixed"
    if missing:
        return "missing_edges"
    if extra:
        return "extra_edges"
    return "reversed_edges"


def _edges(pairs: set[tuple[StableId, StableId]]) -> tuple[CausalEdge, ...]:
    return tuple(CausalEdge(parent_id=parent, child_id=child) for parent, child in sorted(pairs))
