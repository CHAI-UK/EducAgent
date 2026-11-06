"""Shared authoring-test operations; never bypass the experiment's scored gate."""

from educagent_sdk.experiments import CommitExperimentPrediction, ReflectOnExperiment, RunExperiment


def finish_current_experiment(controller):
    state = controller.view()
    activity = next(item for item in controller.pack.activities if item.activity_id == state["activity_id"])
    spec = activity.experiment
    if spec is None:
        return
    base = spec.initial_config

    def action(value, suffix):
        view = controller.view()
        return controller.submit_experiment_action(
            request_id=f"{view['attempt_id']}.experiment.{suffix}", attempt_id=view["attempt_id"],
            experiment_id=spec.experiment_id, input_revision=view["experiment"]["revision"], action=value,
        )

    for index in range(spec.min_distinct_runs):
        field = "target_high_pct" if base.kind == "effect" else "cue_accuracy_pct"
        config = base.model_copy(update={field: (getattr(base, field) + 10 * index) % 110})
        action(CommitExperimentPrediction(config=config, prediction="I expect the chosen setting to change the comparison."), f"predict.{index}")
        action(RunExperiment(), f"run.{index}")
    action(ReflectOnExperiment(reflection="I compared the two settings and their computed outcomes; the result is limited to the declared model."), "reflect")
