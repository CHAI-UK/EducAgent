"""Replayable, content-authored M1 experiments; no model or random execution.

The renderer submits settings and an unscored prediction, never a result.
These two bounded teaching worlds deliberately do not execute arbitrary code.
"""

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StringConstraints

from .contracts import (
    ComparisonTable, ContractModel, EffectExperimentConfig, EffectExperimentModel,
    ExperimentConfig, ExperimentWorkbench, NonEmptyText, ShiftExperimentConfig,
    ShiftExperimentModel, StableId,
)


ExperimentText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=800)]


class CommitExperimentPrediction(ContractModel):
    kind: Literal["commit_prediction"] = "commit_prediction"
    config: ExperimentConfig
    prediction: ExperimentText


class RunExperiment(ContractModel):
    kind: Literal["run"] = "run"


class ReflectOnExperiment(ContractModel):
    kind: Literal["reflect"] = "reflect"
    reflection: ExperimentText


ExperimentAction: TypeAlias = Annotated[
    CommitExperimentPrediction | RunExperiment | ReflectOnExperiment,
    Field(discriminator="kind"),
]


class ExperimentMetric(ContractModel):
    label: NonEmptyText
    value: float
    display_value: NonEmptyText


class ExperimentCase(ContractModel):
    case_id: int
    source_text: NonEmptyText
    generated_text: NonEmptyText
    target: int
    prediction: int
    cue: int
    measurement: int
    emitted: bool
    metadata_known: bool
    source_consistent: bool
    unsupported_addition: bool


class ExperimentResult(ContractModel):
    title: NonEmptyText
    summary: NonEmptyText
    metrics: tuple[ExperimentMetric, ...]
    bars: tuple[ExperimentMetric, ...]
    tables: tuple[ComparisonTable, ...]
    cases: tuple[ExperimentCase, ...] = ()


class ExperimentRun(ContractModel):
    run_id: int = Field(ge=1)
    model_version: Literal["1.0.0"] = "1.0.0"
    config: ExperimentConfig
    prediction: ExperimentText
    result: ExperimentResult


class ExperimentSnapshot(ContractModel):
    experiment_id: StableId
    revision: int = Field(ge=0)
    phase: Literal["configure", "predicted", "result", "reflected"]
    config: ExperimentConfig
    prediction: ExperimentText | None = None
    reflection: ExperimentText | None = None
    runs: tuple[ExperimentRun, ...] = ()
    result: ExperimentResult | None = None


def initial_experiment_snapshot(spec: ExperimentWorkbench) -> ExperimentSnapshot:
    return ExperimentSnapshot(experiment_id=spec.experiment_id, revision=0,
                              phase="configure", config=spec.initial_config)


def apply_experiment_action(
    spec: ExperimentWorkbench, snapshot: ExperimentSnapshot,
    action: ExperimentAction, *, input_revision: int,
) -> ExperimentSnapshot:
    """Apply one checked edit, run, or reflection to an immutable artifact."""
    if snapshot.experiment_id != spec.experiment_id:
        raise ValueError("experiment snapshot belongs to another experiment")
    if input_revision != snapshot.revision:
        raise ValueError("experiment action uses a stale revision")
    update = {"revision": snapshot.revision + 1}
    if isinstance(action, CommitExperimentPrediction):
        if action.config.kind != spec.model.kind:
            raise ValueError("experiment configuration belongs to another model")
        update.update(config=action.config, prediction=action.prediction,
                      phase="predicted", result=None, reflection=None)
    elif isinstance(action, RunExperiment):
        if snapshot.phase != "predicted" or snapshot.prediction is None:
            raise ValueError("record a prediction for this setup before running")
        result = _simulate(spec, snapshot.config)
        run = ExperimentRun(run_id=len(snapshot.runs) + 1, config=snapshot.config,
                            prediction=snapshot.prediction, result=result)
        update.update(phase="result", result=result, runs=(*snapshot.runs, run))
    else:
        if snapshot.phase not in {"result", "reflected"} or snapshot.result is None:
            raise ValueError("run the current setup before comparing its result")
        if _distinct_runs(snapshot) < spec.min_distinct_runs:
            raise ValueError("compare runs from different settings before reflecting")
        update.update(phase="reflected", reflection=action.reflection)
    return snapshot.model_copy(update=update)


def experiment_ready_for_assessment(
    spec: ExperimentWorkbench, snapshot: ExperimentSnapshot,
) -> bool:
    return (snapshot.experiment_id == spec.experiment_id
            and snapshot.phase == "reflected" and bool(snapshot.reflection)
            and snapshot.result is not None
            and _distinct_runs(snapshot) >= spec.min_distinct_runs)


def experiment_view(
    spec: ExperimentWorkbench, snapshot: ExperimentSnapshot, instruction: str,
) -> dict:
    """One phase-visible projection shared by the renderer and tutor.

    Model coefficients, unrun results and scored answer keys are not projected.
    Full history stays in the event trace; only recent runs enter chat context.
    """
    if snapshot.experiment_id != spec.experiment_id:
        raise ValueError("experiment snapshot belongs to another experiment")
    legal = ["commit_prediction"]
    if snapshot.phase == "predicted":
        legal.append("run")
    if snapshot.result is not None and _distinct_runs(snapshot) >= spec.min_distinct_runs:
        legal.append("reflect")
    view = {
        "experiment_id": spec.experiment_id, "title": spec.title,
        "instruction": instruction, "revision": snapshot.revision,
        "phase": snapshot.phase, "config": snapshot.config.model_dump(mode="json"),
        "parameters": _parameters(spec, snapshot.config),
        "prediction": snapshot.prediction, "reflection": snapshot.reflection,
        "runs": [run.model_dump(mode="json") for run in snapshot.runs[-6:]],
        "result": None if snapshot.result is None else snapshot.result.model_dump(mode="json"),
        "legal_actions": legal, "can_submit_check": experiment_ready_for_assessment(spec, snapshot),
        "min_distinct_runs": spec.min_distinct_runs, "distinct_runs": _distinct_runs(snapshot),
    }
    if spec.guide is not None:
        # Keep a distinct comparison available after repeated identical runs.
        # This bounds only the read-only view, never experiments or the trace.
        representatives = {}
        for run in reversed(snapshot.runs):
            representatives.setdefault(run.config.model_dump_json(), run)
            if len(representatives) >= spec.min_distinct_runs:
                break
        retained = {run.run_id: run for run in (*snapshot.runs[-4:], *representatives.values())}
        view["runs"] = [retained[key].model_dump(mode="json") for key in sorted(retained)]
        view["guide"] = spec.guide.model_dump(mode="json")
        view["parameters"] = [parameter for parameter in view["parameters"]
                              if parameter["parameter_id"] == spec.guide.parameter_id]
        if view["result"] is not None:
            view["result"] = _guided_result_view(spec, view["result"])
        for run in view["runs"]:
            run["result"] = _guided_result_view(spec, run["result"])
    return view


def _guided_result_view(spec: ExperimentWorkbench, result: dict) -> dict:
    """Present one authored task without rewriting the full recorded result."""
    guide = spec.guide
    assert guide is not None
    labels = {metric.metric_label: metric.label for metric in guide.metrics}
    by_label = {metric["label"]: metric for metric in result["metrics"]}
    visible_metrics = [by_label[label] for label in labels]
    view = {**result, "metrics": visible_metrics, "bars": [], "tables": []}
    view["title"] = {
        "intervention": "Programme comparison result",
        "prediction": "Prediction result",
        "generation": "Report-generation result",
    }[guide.section]
    view["summary"] = "; ".join(
        f"{labels[metric['label']]}: {metric['display_value']}" for metric in visible_metrics
    ) + ". These results describe this teaching setup, not a guarantee for another setting."
    if guide.section == "intervention":
        # Assignment practice explicitly asks learners to compare starting-group
        # counts. Keep that computed evidence, without the wider rates appendix.
        source = next(table for table in result["tables"] if table["table_id"] == "source-cohort")
        view["tables"] = [{
            "table_id": "starting-group-counts", "label": "Starting groups in this test",
            "columns": ["Starting group", "Programme A count", "Programme B count"],
            "rows": [[row[0], row[1], row[4]] for row in source["rows"][:-1]],
            "note": "The source cohort stays at 1,000 people. These counts show who received each programme, not the target-population weights.",
        }]
    elif guide.section == "prediction":
        view["cases"] = [{key: case[key] for key in
                          ("case_id", "target", "prediction", "cue", "measurement")}
                         for case in result["cases"]]
    return view


def _distinct_runs(snapshot: ExperimentSnapshot) -> int:
    return len({run.config.model_dump_json() for run in snapshot.runs})


def _metric(label: str, value: float, unit: str = "%") -> ExperimentMetric:
    rounded = round(value, 4)
    return ExperimentMetric(label=label, value=rounded, display_value=f"{rounded:g}{unit}")


def _table(table_id: str, label: str, columns: tuple[str, ...], rows: list[tuple[str, ...]], note: str) -> ComparisonTable:
    return ComparisonTable(table_id=table_id, label=label, columns=columns, rows=tuple(rows), note=note)


def _simulate(spec: ExperimentWorkbench, config: ExperimentConfig) -> ExperimentResult:
    if isinstance(spec.model, EffectExperimentModel) and isinstance(config, EffectExperimentConfig):
        return _effect(spec.model, config)
    if isinstance(spec.model, ShiftExperimentModel) and isinstance(config, ShiftExperimentConfig):
        return _shift(spec.model, config)
    raise ValueError("experiment model and configuration do not match")


def _effect(model: EffectExperimentModel, config: EffectExperimentConfig) -> ExperimentResult:
    # The source cohort remains fixed. Target weights never rewrite source rows.
    high_a = model.selected_high_a_pct / 100 if config.assignment == "self_selected" else 0.5
    high_b = model.selected_high_b_pct / 100 if config.assignment == "self_selected" else 0.5
    a_source = (1 - high_a) * model.a_low + high_a * model.a_high
    b_source = (1 - high_b) * model.b_low + high_b * model.b_high
    target_high = config.target_high_pct / 100
    a_target = (1 - target_high) * model.a_low + target_high * model.a_high
    b_target = (1 - target_high) * model.b_low + target_high * model.b_high
    source_diff, target_diff = 100 * (a_source - b_source), 100 * (a_target - b_target)
    selected_a, selected_b = ((a_source, b_source) if config.analysis == "pooled" else (a_target, b_target))
    rows = []
    for label, n_a, rate_a, n_b, rate_b in (
        (model.low_label, 500 * (1 - high_a), model.a_low, 500 * (1 - high_b), model.b_low),
        (model.high_label, 500 * high_a, model.a_high, 500 * high_b, model.b_high),
    ):
        rows.append((label, f"{n_a:g}", f"{n_a * rate_a:g}", f"{100 * rate_a:g}%",
                     f"{n_b:g}", f"{n_b * rate_b:g}", f"{100 * rate_b:g}%"))
    rows.append(("All source records", "500", f"{500 * a_source:g}", f"{100 * a_source:g}%",
                 "500", f"{500 * b_source:g}", f"{100 * b_source:g}%"))
    return ExperimentResult(
        title="Programme experiment result",
        summary=(f"The source pooled A-minus-B contrast is {source_diff:+.1f} percentage points. "
                 f"Standardizing both programmes to a target with {config.target_high_pct}% in {model.high_label.lower()} "
                 f"gives {target_diff:+.1f} percentage points. These are exact expectations in the declared teaching model, "
                 "not a sampled clinical trial or evidence that the assumptions are true."),
        metrics=(_metric("Source pooled A minus B", source_diff, " pp"),
                 _metric("Target-standardized A minus B", target_diff, " pp"),
                 _metric("Selected analysis contrast", 100 * (selected_a - selected_b), " pp")),
        bars=(_metric(model.treatment_a_label, 100 * selected_a), _metric(model.treatment_b_label, 100 * selected_b)),
        tables=(
            _table("source-cohort", "Computed source cohort", ("Baseline", "A count", "A expected successes", "A rate", "B count", "B expected successes", "B rate"), rows,
                   f"Fixed source: 1,000 people, 500 per baseline group. Outcome: {model.outcome_label}. Assignment changes the treatment mixture, not the success mechanisms."),
            _table("target-comparison", "Computed common target population", ("Programme", "Lower-group weight", "Higher-group weight", "Expected success rate"),
                   [(model.treatment_a_label, f"{100 - config.target_high_pct}%", f"{config.target_high_pct}%", f"{100 * a_target:g}%"),
                    (model.treatment_b_label, f"{100 - config.target_high_pct}%", f"{config.target_high_pct}%", f"{100 * b_target:g}%")],
                   "The target estimate assumes adequate baseline adjustment, overlap, consistency and stable within-stratum mechanisms. A source randomization does not guarantee the target assumptions."),
        ),
    )


def _shift(model: ShiftExperimentModel, config: ShiftExperimentConfig) -> ExperimentResult:
    correct = emitted = supported = unsupported = contradicted = 0
    conditional = [[0, 0], [0, 0]]
    all_cases = []
    for index in range(100):
        target = index % 2
        # Coprime permutations spread deterministic corruptions over both labels.
        cue = target if (index * 37) % 100 < config.cue_accuracy_pct else 1 - target
        measurement = 1 - target if (index * 53 + 17) % 100 < config.measurement_error_pct else target
        if config.flip_cue:
            cue = 1 - cue
        prediction = cue if config.predictor == "cue" else measurement
        known = (index * 29 + 11) % 100 < config.metadata_available_pct
        source_flag = model.source_positive if measurement else model.source_negative
        source = f"{source_flag} {model.qualifier if known else 'Required context is not recorded.'}"
        output = config.generator == "fluent" or known
        output_flag = prediction if config.generator == "fluent" else measurement
        addition = bool(output and not known)
        consistent = bool(output and output_flag == measurement)
        draft = (f"{model.source_positive if output_flag else model.source_negative} "
                 f"{model.qualifier if known else model.unsupported_detail}" if output else
                 "Full report withheld: the source does not record the required context.")
        correct += prediction == target
        emitted += output
        supported += output and consistent and not addition
        unsupported += addition
        contradicted += output and not consistent
        conditional[target][0] += prediction == target
        conditional[target][1] += 1
        all_cases.append(ExperimentCase(
            case_id=index + 1, source_text=source, generated_text=draft,
            target=target, prediction=prediction, cue=cue, measurement=measurement,
            emitted=output, metadata_known=known, source_consistent=consistent,
            unsupported_addition=addition,
        ))
    emitted_support = 100 * supported / emitted if emitted else 0.0
    return ExperimentResult(
        title="Prediction and report experiment result",
        summary=(f"Prediction agrees with the independent reference in {correct}/100 cases. "
                 f"{emitted}/100 full reports are emitted; {supported}/100 are complete and source-supported. "
                 "Source-faithful reporting is judged against the measured source, not independent reference truth. "
                 "A cue edit changes inputs, never the reference outcome. These are declared simulator results, not deployment guarantees."),
        metrics=(_metric("Reference prediction accuracy", float(correct)),
                 _metric("Complete source-supported reports / all cases", float(supported)),
                 _metric("Full-report coverage", float(emitted)),
                 _metric("Source-supported / emitted reports", emitted_support) if emitted else
                 ExperimentMetric(label="Source-supported / emitted reports", value=0.0, display_value="Not defined: no reports emitted"),
                 _metric("Reports with unsupported additions / all cases", float(unsupported)),
                 _metric("Reports contradicting source flag / all cases", float(contradicted))),
        bars=(_metric("Reference accuracy", float(correct)), _metric("Source-supported reports", float(supported)), _metric("Full-report coverage", float(emitted))),
        tables=(
            _table("conditional-performance", "Reference-conditional prediction checks", ("Reference group", "Correct predictions", "Group size", "Accuracy"),
                   [(f"Reference {label}", str(counts[0]), str(counts[1]), f"{100 * counts[0] / counts[1]:g}%")
                    for label, counts in enumerate(conditional)],
                   "Both reference groups contain 50 cases. Stable aggregate scores alone do not establish causal invariance or cover untested measurement changes."),
            _table("report-fidelity", "Computed report checks", ("Check", "Count / 100 cases"),
                   [("Full reports emitted", str(emitted)), ("Complete source-supported reports", str(supported)),
                    ("Unsupported additions", str(unsupported)), ("Source contradictions", str(contradicted))],
                   "Contradictions and unsupported additions can overlap; do not add them as disjoint errors. Withholding a full report reduces coverage rather than inventing missing context."),
        ),
        # Include representative failures and abstentions, not only easy first rows.
        cases=tuple(all_cases[index] for index in dict.fromkeys((0, 1, 2, 3, 24, 49, 74, 99))),
    )


def _parameters(spec: ExperimentWorkbench, config: ExperimentConfig) -> list[dict]:
    def choice(key, label, options):
        return {"parameter_id": key, "label": label, "kind": "choice",
                "value": getattr(config, key), "options": [{"option_id": value, "label": text} for value, text in options]}

    def percent(key, label):
        return {"parameter_id": key, "label": label, "kind": "range",
                "value": getattr(config, key), "min": 0, "max": 100, "step": 10, "unit": "%"}

    if isinstance(config, EffectExperimentConfig):
        return [choice("assignment", "Programme assignment", [("self_selected", "People choose their programme"), ("randomized", "Balanced random assignment")]),
                percent("target_high_pct", f"Target population: {spec.model.high_label.lower()}"),
                choice("analysis", "Contrast shown in the chart", [("pooled", "Source pooled comparison"), ("standardized", "Same target weights for A and B")])]
    return [choice("predictor", "Prediction rule", [("cue", "Use the site cue"), ("content", "Use the content measurement")]),
            percent("cue_accuracy_pct", "Environment: cue agrees with reference before cue edit"),
            percent("measurement_error_pct", "Environment: content measurement error"),
            percent("metadata_available_pct", "Required report context available"),
            {"parameter_id": "flip_cue", "label": "Edit the cue while keeping reference and content fixed", "kind": "toggle", "value": config.flip_cue},
            choice("generator", "Report-generation rule", [("fluent", "Complete every report, filling missing context"), ("grounded", "Preserve source facts; withhold if context is missing")])]
