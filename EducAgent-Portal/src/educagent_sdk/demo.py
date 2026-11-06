"""Small local-demo controller and JSONL event store for the headless SDK."""

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import TypeAdapter
from pydantic_ai.models import Model

from .causal_scene import (
    CausalSceneAction,
    legal_scene_action_kinds,
    legal_scene_focus_ids,
    scene_text_projection,
)
from .contracts import Activity, ContentPack, StableId
from .umbrella_simulation import public_simulation_view
from .evaluation import CausalSceneEvidence, ChoiceEvidence, ClassificationEvidence
from .experiments import ExperimentAction, experiment_ready_for_assessment, experiment_view
from .events import (
    AttemptClosed,
    AttemptStarted,
    ExperimentActionRecorded,
    LearnerMessage,
    LearnerMessageRecorded,
    LearningEvent,
    ResponseRecorded,
    SupportRequest,
    SupportRequested,
    TeachingMoveSelected,
    can_complete_attempt,
    close_attempt,
    complete_session,
    next_required_activity,
    record_choice_response,
    record_causal_scene_action,
    record_causal_scene_evidence,
    record_classification_response,
    record_learner_message,
    record_experiment_action,
    record_support_request,
    recover_pending_turn,
    replay,
    selected_move_for_request,
    select_fixed_policy_move,
    start_attempt,
    start_session,
)
from .profiles import policy_learner_view, project_learner_profile
from .release import validate_release
from .tutor import run_open_demo_reply, run_tutor_turn
from .tutor_examples import AdjustmentExampleRoles, example_roles_from_reply
from .turns import ResolvedTutorTurn, compose_tutor_turn


def _assessment_signature(activity: Activity) -> tuple[object, ...]:
    """Fields that define scored evidence, coverage, revision and support scope."""

    return (
        activity.activity_id, activity.concept_id, activity.covered_concept_ids,
        activity.activity_type, activity.is_transfer, activity.requires_revision,
        activity.causal_scene_id,
        activity.experiment,
        tuple((choice.option_id, choice.correct, choice.misconception_id,
               len(choice.hint_resource_ids)) for choice in activity.choices),
    )


class JsonlEventStore:
    """The deliberately small second event-store implementation for local demos."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._adapter = TypeAdapter(LearningEvent)

    def load(self) -> list[LearningEvent]:
        if not self.path.exists():
            return []
        events = [
            self._adapter.validate_json(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if events:
            replay(events)
        return events

    def append(self, events: list[LearningEvent]) -> None:
        if not events:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            for event in events:
                handle.write(event.model_dump_json())
                handle.write("\n")

    def reset(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")


class DemoController:
    """Local API boundary with fixed-policy or guarded-tutor selection."""

    def __init__(
        self,
        pack: ContentPack,
        *,
        store: JsonlEventStore | None = None,
        mode: Literal["fixed_policy_control", "guarded_tutor"] = "fixed_policy_control",
        profile_id: Literal["general", "medical"] | None = None,
        teaching_pack: ContentPack | None = None,
    ) -> None:
        self.pack = pack
        if profile_id not in {None, "general", "medical"}:
            raise ValueError("unknown learner profile")
        self._teaching_pack = pack if teaching_pack is None else teaching_pack
        lesson_profiles = {
            lesson.profile_id for lesson in self._teaching_pack.lessons
        }
        if self._teaching_pack.lesson is not None:
            lesson_profiles.add(self._teaching_pack.lesson.profile_id)
        self._profile_id = profile_id
        if lesson_profiles:
            if profile_id is not None and profile_id not in lesson_profiles:
                raise ValueError("teaching pack must match the fixed learner profile")
            if profile_id is None:
                self._profile_id = next(iter(lesson_profiles))
        if teaching_pack is not None:
            validate_release(teaching_pack)
            if teaching_pack.concepts != pack.concepts or (
                tuple(_assessment_signature(item) for item in teaching_pack.activities)
                != tuple(_assessment_signature(item) for item in pack.activities)
            ) or teaching_pack.causal_scenes != pack.causal_scenes:
                raise ValueError("teaching pack must preserve the scored curriculum and assessment contract")
        self.store = store
        self.mode = mode
        self.events = [] if store is None else store.load()
        if self.events:
            state = replay(self.events)
            if state.pack_id != pack.pack_id or state.pack_version != pack.version:
                raise ValueError("stored demo events belong to a different content pack")

    @property
    def profile_id(self) -> Literal["general", "medical"] | None:
        """The explicit audience fixed when this controller was created."""

        return self._profile_id

    @property
    def teaching_pack(self) -> ContentPack:
        """A fixed read-only teaching catalog; the scored pack remains authoritative."""

        return self._teaching_pack

    def start(
        self,
        *,
        session_id: StableId = "demo.session.01",
        preferred_activity_ids: tuple[StableId, ...] = (),
        route_scope: Literal["all", "preferred"] = "all",
    ) -> dict[str, Any]:
        if self.events:
            return self.view()
        self._mutate(
            lambda: start_session(
                self.events,
                self.pack,
                session_id=session_id,
                preferred_activity_ids=preferred_activity_ids,
                route_scope=route_scope,
            )
        )
        if next_required_activity(self.pack, self._state()) is None:
            self._mutate(
                lambda: complete_session(
                    self.events,
                    self.pack,
                    request_id=f"{session_id}.targeted.complete",
                )
            )
        else:
            self._mutate(
                lambda: start_attempt(
                    self.events,
                    self.pack,
                    attempt_id=f"{session_id}.attempt.01",
                )
            )
        return self.view()

    async def start_with_tutor(
        self,
        *,
        model: Model | str,
        session_id: StableId = "demo.session.01",
        preferred_activity_ids: tuple[StableId, ...] = (),
        route_scope: Literal["all", "preferred"] = "all",
    ) -> dict[str, Any]:
        """Start one route, then let the tutor orient the new attempt."""

        self.start(
            session_id=session_id,
            preferred_activity_ids=preferred_activity_ids,
            route_scope=route_scope,
        )
        await self._orient_with_tutor(model=model)
        return self.view()

    def respond(self, *, request_id: StableId, option_id: StableId) -> dict[str, Any]:
        if not self._record_response(request_id=request_id, option_id=option_id):
            return self.view()
        self._mutate(
            lambda: select_fixed_policy_move(
                self.events, self.pack, request_id=request_id
            )
        )
        return self.view()

    async def respond_with_tutor(
        self,
        *,
        request_id: StableId,
        option_id: StableId,
        model: Model | str,
    ) -> dict[str, Any]:
        """Record scored evidence, then let the guarded tutor select one legal move."""

        if not self._record_response(request_id=request_id, option_id=option_id):
            return self.view()
        await self._select_with_tutor(request_id=request_id, model=model)
        return self.view()

    async def send_message_with_tutor(
        self,
        *,
        request_id: StableId,
        text: str,
        model: Model | str,
        unguarded: bool = False,
    ) -> dict[str, Any]:
        """Record free learner text before the guarded tutor selects a legal move."""

        prior = self._input_for_request(request_id)
        if prior is None:
            self._record_learner_message(request_id=request_id, text=text)
        elif (
            not isinstance(prior, LearnerMessageRecorded)
            or prior.payload.message != LearnerMessage(text=text)
        ):
            raise ValueError("request_id was reused with different content")
        elif selected_move_for_request(self.events, request_id) is not None:
            return self.view()
        if unguarded:
            start = len(self.events)
            await run_open_demo_reply(
                self.events, self.pack, request_id=request_id, model=model,
                profile_id=self.profile_id, teaching_pack=self.teaching_pack,
            )
            if self.store is not None:
                self.store.append(self.events[start:])
        else:
            await self._select_with_tutor(request_id=request_id, model=model)
        return self.view()

    def submit_experiment_action(
        self, *, request_id: StableId, attempt_id: StableId,
        experiment_id: StableId, input_revision: int, action: ExperimentAction,
    ) -> dict[str, Any]:
        """Record an unscored experiment operation without requesting a model."""

        self._mutate(lambda: record_experiment_action(
            self.events, self.pack, request_id=request_id, attempt_id=attempt_id,
            experiment_id=experiment_id, input_revision=input_revision, action=action,
        ))
        return self.view()

    def submit_scene_action(
        self,
        *,
        request_id: StableId,
        input_revision: int,
        action: CausalSceneAction,
    ) -> dict[str, Any]:
        """Record one declared causal-object action; it is never scored evidence."""

        state = self._state()
        if state.open_attempt_id is None:
            raise ValueError("the demo is not ready for a causal-scene action")
        self._mutate(
            lambda: record_causal_scene_action(
                self.events,
                self.pack,
                attempt_id=state.open_attempt_id,
                request_id=request_id,
                action=action,
                input_revision=input_revision,
            )
        )
        return self.view()

    async def submit_scene_action_with_tutor(
        self,
        *,
        request_id: StableId,
        input_revision: int,
        action: CausalSceneAction,
        model: Model | str,
    ) -> dict[str, Any]:
        """Record the learner action before the guarded tutor directs the next one."""

        self.submit_scene_action(
            request_id=request_id,
            input_revision=input_revision,
            action=action,
        )
        await self._select_with_tutor(request_id=request_id, model=model)
        return self.view()

    async def submit_scene_evidence_with_tutor(
        self,
        *,
        request_id: StableId,
        model: Model | str,
    ) -> dict[str, Any]:
        """Submit the completed revision artifact to the causal-scene evaluator."""

        state = self._state()
        if state.open_attempt_id is None:
            raise ValueError("the demo is not ready for causal-scene evidence")
        self._mutate(
            lambda: record_causal_scene_evidence(
                self.events,
                self.pack,
                attempt_id=state.open_attempt_id,
                request_id=request_id,
            )
        )
        await self._select_with_tutor(request_id=request_id, model=model)
        return self.view()

    def _record_response(self, *, request_id: StableId, option_id: StableId) -> bool:
        """Append one response unless an identical completed request already exists."""

        prior = self._input_for_request(request_id)
        if prior is not None:
            if (
                not isinstance(prior, ResponseRecorded)
                or _response_option_id(prior) != option_id
            ):
                raise ValueError("request_id was reused with different content")
            return selected_move_for_request(self.events, request_id) is None
        state = self._state()
        activity = self._current_activity(state.current_activity_id)
        if state.phase != "awaiting_response" or state.open_attempt_id is None:
            raise ValueError("the demo is not ready for a learner response")

        if activity.activity_type == "choice":
            self._mutate(
                lambda: record_choice_response(
                    self.events,
                    self.pack,
                    attempt_id=state.open_attempt_id,
                    request_id=request_id,
                    evidence=ChoiceEvidence(
                        activity_id=activity.activity_id,
                        option_id=option_id,
                    ),
                    curriculum_requirements_met=True,
                )
            )
        else:
            prior = self._current_classification_response(state.open_attempt_id)
            artifact_id = state.classification_artifact_id or (
                f"{state.open_attempt_id}.artifact"
            )
            self._mutate(
                lambda: record_classification_response(
                    self.events,
                    self.pack,
                    attempt_id=state.open_attempt_id,
                    request_id=request_id,
                    evidence=ClassificationEvidence(
                        activity_id=activity.activity_id,
                        classification_id=option_id,
                        artifact_id=artifact_id,
                        revises_evidence_event_id=(
                            None if prior is None else prior.event_id
                        ),
                    ),
                    curriculum_requirements_met=True,
                )
            )

        return True

    def _record_learner_message(self, *, request_id: StableId, text: str) -> bool:
        """Append one bounded learner message unless its request already completed."""

        message = LearnerMessage(text=text)
        if selected_move_for_request(self.events, request_id) is not None:
            prior = self._input_for_request(request_id)
            if (
                not isinstance(prior, LearnerMessageRecorded)
                or prior.payload.message != message
            ):
                raise ValueError("request_id was reused with different content")
            return False
        state = self._state()
        if state.phase != "awaiting_response" or state.open_attempt_id is None:
            if state.pending_request_id is not None:
                raise ValueError(
                    f"retry pending tutor request {state.pending_request_id} "
                    "before sending another message"
                )
            raise ValueError("the demo is not ready for a learner message")
        self._mutate(
            lambda: record_learner_message(
                self.events,
                self.pack,
                attempt_id=state.open_attempt_id,
                request_id=request_id,
                message=message,
            )
        )
        return True

    def request_explanation(self, *, request_id: StableId) -> dict[str, Any]:
        if not self._record_explanation_request(request_id=request_id):
            return self.view()
        self._mutate(
            lambda: select_fixed_policy_move(
                self.events, self.pack, request_id=request_id
            )
        )
        return self.view()

    async def request_explanation_with_tutor(
        self,
        *,
        request_id: StableId,
        model: Model | str,
    ) -> dict[str, Any]:
        """Record an unscored support request, then select a guarded tutor move."""

        if not self._record_explanation_request(request_id=request_id):
            return self.view()
        await self._select_with_tutor(request_id=request_id, model=model)
        return self.view()

    async def _select_with_tutor(
        self, *, request_id: StableId, model: Model | str
    ) -> None:
        """Persist the guarded selector's event with the same boundary as input."""

        start = len(self.events)
        await run_tutor_turn(
            self.events,
            self.pack,
            request_id=request_id,
            model=model,
        )
        if self.store is not None:
            self.store.append(self.events[start:])

    def _record_explanation_request(self, *, request_id: StableId) -> bool:
        """Append one explanation request unless an identical request already has a move."""

        prior = self._input_for_request(request_id)
        if prior is not None:
            if (
                not isinstance(prior, SupportRequested)
                or prior.payload.request != SupportRequest(kind="explanation")
            ):
                raise ValueError("request_id was reused with different content")
            return selected_move_for_request(self.events, request_id) is None
        state = self._state()
        if state.phase != "awaiting_response" or state.open_attempt_id is None:
            raise ValueError("the demo is not ready for a support request")
        self._mutate(
            lambda: record_support_request(
                self.events,
                self.pack,
                attempt_id=state.open_attempt_id,
                request_id=request_id,
                request=SupportRequest(kind="explanation"),
            )
        )
        return True

    def continue_activity(self, *, request_id: StableId) -> dict[str, Any]:
        if any(
            isinstance(event, AttemptClosed) and event.request_id == request_id
            for event in self.events
        ):
            return self.view()
        state = self._state()
        if state.completion_evidence_event_id is None:
            raise ValueError("the current activity cannot advance yet")
        if state.pending_request_id is not None:
            # Optional discussion may fail after the answer was already checked.
            # Close its saved input with a traceable hold before leaving the task.
            self._mutate(
                lambda: recover_pending_turn(
                    self.events,
                    self.pack,
                    request_id=state.pending_request_id,
                )
            )
            state = self._state()
        if not can_complete_attempt(state):
            raise ValueError("the current activity cannot advance yet")
        assert state.current_activity_id is not None
        current_activity_id = state.current_activity_id
        current_concept_id = self._current_activity(
            current_activity_id
        ).concept_id
        self._mutate(
            lambda: close_attempt(
                self.events,
                self.pack,
                attempt_id=state.open_attempt_id,
                status="completed",
                request_id=request_id,
            )
        )
        state = self._state()
        route_activity_ids = (
            set(state.preferred_activity_ids)
            if state.route_scope == "preferred"
            and current_activity_id in state.preferred_activity_ids
            else {activity.activity_id for activity in self.pack.activities}
        )
        completed_activity_ids = set(state.completed_activity_ids)
        next_activity = next(
            (
                activity
                for activity in self.pack.activities
                if activity.concept_id == current_concept_id
                and activity.activity_id.startswith(f"{current_concept_id}.")
                and activity.activity_id in route_activity_ids
                and activity.activity_id not in completed_activity_ids
            ),
            None,
        )
        if next_activity is None:
            next_activity = next_required_activity(self.pack, state)
        if next_activity is None:
            self._mutate(
                lambda: complete_session(
                    self.events, self.pack, request_id=f"{request_id}.complete"
                )
            )
        else:
            self._mutate(
                lambda: start_attempt(
                    self.events,
                    self.pack,
                    attempt_id=self._next_attempt_id(state.session_id),
                    activity_id=next_activity.activity_id,
                )
            )
        return self.view()

    async def continue_activity_with_tutor(
        self, *, request_id: StableId, model: Model | str
    ) -> dict[str, Any]:
        """Advance through a licensed gate, then orient the next attempt."""

        self.continue_activity(request_id=request_id)
        await self._orient_with_tutor(model=model)
        return self.view()

    async def _orient_with_tutor(self, *, model: Model | str) -> None:
        """Persist one unscored tutor-led opening without fabricating learner input."""

        state = self._state()
        if state.status != "active" or state.open_attempt_id is None:
            return
        request_id = f"{state.open_attempt_id}.orientation"
        if selected_move_for_request(self.events, request_id) is not None:
            return
        self._mutate(
            lambda: record_support_request(
                self.events,
                self.pack,
                attempt_id=state.open_attempt_id,
                request_id=request_id,
                request=SupportRequest(kind="orientation"),
            )
        )
        await self._select_with_tutor(request_id=request_id, model=model)

    def topic_activity_ids(self, concept_id: StableId) -> tuple[StableId, ...]:
        """Return the authored lesson questions, not later experiments or finals."""

        lessons = self.teaching_pack.lessons + (
            () if self.teaching_pack.lesson is None else (self.teaching_pack.lesson,)
        )
        lesson = next((item for item in lessons if item.concept_id == concept_id), None)
        if lesson is not None:
            return tuple(dict.fromkeys((lesson.practice_activity_id, lesson.challenge_activity_id)))
        return tuple(
            activity.activity_id for activity in self.pack.activities
            if activity.concept_id == concept_id
            and activity.activity_id.startswith(f"{concept_id}.")
        )

    def final_activity_ids(self) -> tuple[StableId, ...]:
        """Return the authored capstone questions without inventing a concept."""

        return tuple(activity.activity_id for activity in self.pack.activities
                     if activity.workbench is not None and activity.workbench.stage == "capstone")

    def navigate_to_final_check(self, *, request_id: StableId) -> dict[str, Any]:
        """Open the first unfinished final question through the normal navigation gate."""

        state = self._state()
        if state.status != "active":
            raise ValueError("start the learning route before navigating to its final check")
        final_ids = self.final_activity_ids()
        if not final_ids:
            raise ValueError("this course has no final check")
        completed = set(state.completed_activity_ids)
        target = next((activity for activity in self.pack.activities
                       if activity.activity_id in final_ids and activity.activity_id not in completed), None)
        return self._navigate_to_activity(request_id=request_id, target=target)

    def navigate_to_concept(
        self,
        *,
        request_id: StableId,
        concept_id: StableId,
    ) -> dict[str, Any]:
        """Move to an unfinished authored activity without granting completion."""

        state = self._state()
        if state.status != "active":
            raise ValueError("the learning route is already complete")
        activity_ids = self.topic_activity_ids(concept_id)
        activities = tuple(
            activity for activity in self.pack.activities if activity.activity_id in activity_ids
        )
        if not activities:
            raise ValueError("unknown concept_id")
        completed = set(state.completed_activity_ids)
        target = next(
            (activity for activity in activities if activity.activity_id not in completed),
            None,
        )
        return self._navigate_to_activity(request_id=request_id, target=target)

    def _navigate_to_activity(self, *, request_id: StableId, target: Activity | None) -> dict[str, Any]:
        """Share the existing close/start semantics for two authored navigation routes."""

        state = self._state()
        if target is None or target.activity_id == state.current_activity_id:
            return self.view()
        if state.open_attempt_id is not None:
            self._mutate(
                lambda: close_attempt(
                    self.events,
                    self.pack,
                    attempt_id=state.open_attempt_id,
                    status=("completed" if can_complete_attempt(state) else "interrupted"),
                    request_id=request_id,
                )
            )
        state = self._state()
        self._mutate(
            lambda: start_attempt(
                self.events,
                self.pack,
                attempt_id=self._next_attempt_id(state.session_id),
                activity_id=target.activity_id,
            )
        )
        return self.view()

    async def navigate_to_concept_with_tutor(
        self,
        *,
        request_id: StableId,
        concept_id: StableId,
        model: Model | str,
    ) -> dict[str, Any]:
        """Open an authored activity, then let the tutor orient its new attempt."""

        self.navigate_to_concept(request_id=request_id, concept_id=concept_id)
        await self._orient_with_tutor(model=model)
        return self.view()

    def reset(self) -> dict[str, Any]:
        self.events.clear()
        if self.store is not None:
            self.store.reset()
        return self.view()

    def view(self) -> dict[str, Any]:
        final_activity_ids = self.final_activity_ids()
        final_ids = set(final_activity_ids)
        final_check = None if not final_ids else {
            "status": "not_started", "is_current": False,
            "completed_count": 0, "total_count": len(final_ids),
        }
        if not self.events:
            return {
                "status": "not_started",
                "title": self.pack.title,
                "pack_id": self.pack.pack_id,
                "mode": self.mode,
                "assessment_submitted": False,
                "assessment_accepted": False,
                "answer_feedback": None,
                "topic_practice_completed_concept_ids": (),
                "final_check": final_check,
                "final_check_activity_ids": list(final_activity_ids),
            }
        state = self._state()
        activity = (
            None
            if state.current_activity_id is None
            else self._current_activity(state.current_activity_id)
        )
        question = None
        choices: list[dict[str, str]] = []
        if activity is not None:
            question = self._resource_text(activity.question_resource_id)
            activity_index = next(
                index
                for index, authored in enumerate(self.pack.activities)
                if authored.activity_id == activity.activity_id
            )
            displayed_choices = (
                activity.choices
                if activity_index % 2 == 0
                else tuple(reversed(activity.choices))
            )
            choices = [
                {"option_id": choice.option_id, "text": choice.text}
                for choice in displayed_choices
            ]
        scene_view = None
        if activity is not None and state.causal_scene_snapshot is not None:
            scene = next(
                scene
                for scene in self.pack.causal_scenes
                if scene.scene_id == activity.causal_scene_id
            )
            snapshot = state.causal_scene_snapshot
            simulation = public_simulation_view(scene, snapshot)
            has_result = snapshot.intervention_action_id is not None
            visible_nodes = [node for node in scene.nodes if node.initially_visible
                or snapshot.phase in {"model", "prediction", "comparison", "revision"}
                or (scene.simulation is not None and snapshot.phase == "records")]
            visible_node_ids = {node.node_id for node in visible_nodes}
            can_disclose_reference = simulation is None or simulation["ready_for_revision"]
            scene_resources = {
                "hook": self._resource_text(scene.hook_resource_id),
                "records": self._resource_text(scene.records_resource_id) if snapshot.phase != "hook" else "",
                "model": self._resource_text(scene.model_resource_id) if snapshot.phase != "hook" else "",
                "prediction": self._resource_text(scene.prediction_resource_id) if snapshot.phase in {"model", "prediction", "comparison", "revision"} else "",
                "intervention": self._resource_text(scene.intervention_resource_id) if snapshot.phase in {"prediction", "comparison", "revision"} else "",
                "result": self._resource_text(scene.result_resource_id) if has_result else "",
                "reflection": self._resource_text(scene.reflection_resource_id) if has_result and can_disclose_reference else "",
                "direct_explanation": self._resource_text(scene.direct_explanation_resource_id) if has_result and can_disclose_reference else "",
            }
            latest_scene_move = next(
                (
                    event
                    for event in reversed(self.events)
                    if isinstance(event, TeachingMoveSelected)
                    and event.attempt_id == state.open_attempt_id
                    and event.payload.interaction_focus_id is not None
                ),
                None,
            )
            scene_view = {
                "scene_id": scene.scene_id,
                "title": scene.title,
                "phase": snapshot.phase,
                "revision": snapshot.revision,
                "graph_edges": [edge.model_dump() for edge in snapshot.graph_edges],
                "prediction_id": snapshot.prediction_id,
                "intervention_action_id": snapshot.intervention_action_id,
                "reflection": snapshot.reflection,
                "evidence_status": (
                    None
                    if state.last_evaluation is None
                    else ("accepted" if state.last_evaluation.accepted else "rejected")
                ),
                "next_interaction_focus_label": (
                    _scene_focus_label(legal_scene_focus_ids(snapshot)[0])
                    if latest_scene_move is None
                    else _scene_focus_label(latest_scene_move.payload.interaction_focus_id)
                ),
                "nodes": [node.model_dump() for node in visible_nodes],
                "permitted_edges": [edge.model_dump() for edge in scene.permitted_edges
                    if edge.parent_id in visible_node_ids and edge.child_id in visible_node_ids],
                "observed_records": (
                    []
                    if snapshot.phase == "hook"
                    else [record.model_dump() for record in scene.observed_records]
                ),
                "intervention": {
                    "action_id": scene.intervention.action_id,
                    "variable_id": scene.intervention.variable_id,
                    "value": scene.intervention.value,
                    "result_records": ([] if not has_result else [record.model_dump() for record in (
                        snapshot.simulation_runs[-1].reference_result_records
                        if scene.simulation is not None else scene.intervention.result_records
                    )]),
                },
                "predictions": [prediction.model_dump() for prediction in scene.predictions],
                "resources": scene_resources,
                "simulation": simulation,
                "legal_action_kinds": legal_scene_action_kinds(snapshot),
                "text_alternative": scene_text_projection(scene, snapshot),
            }
        pending_message = next(
            (
                event
                for event in reversed(self.events)
                if isinstance(event, LearnerMessageRecorded)
                and event.attempt_id == state.open_attempt_id
                and selected_move_for_request(self.events, event.request_id) is None
            ),
            None,
        )
        last_experiment_edit = next((
            event.sequence for event in reversed(self.events)
            if isinstance(event, ExperimentActionRecorded) and event.attempt_id == state.open_attempt_id
        ), 0)
        assessment = next((
            event for event in reversed(self.events)
            if isinstance(event, ResponseRecorded) and event.attempt_id == state.open_attempt_id
            and event.sequence > last_experiment_edit
        ), None)
        answer_feedback = None
        if assessment is not None and isinstance(
            assessment.payload.evidence, (ChoiceEvidence, ClassificationEvidence)
        ):
            answer_feedback = {
                "accepted": assessment.payload.evaluation.accepted,
                "option_id": _response_option_id(assessment),
                "text": self._resource_text(assessment.payload.evaluation.consequence_resource_id),
            }
        experiment = (
            None if activity is None or activity.experiment is None or state.experiment_snapshot is None
            else experiment_view(
                activity.experiment, state.experiment_snapshot,
                instruction=self._resource_text(activity.experiment.instructions_resource_id),
            )
        )
        if experiment is not None:
            experiment["frozen"] = bool(assessment and assessment.payload.evaluation.accepted)
            if experiment["frozen"]:
                experiment["legal_actions"] = []
        topic_completed = set(state.completed_activity_ids)
        # The current accepted question can finish topic practice before Continue
        # closes its attempt. This projection grants no activity or concept credit.
        if assessment is not None and assessment.payload.evaluation.accepted and assessment.payload.curriculum_requirements_met:
            topic_completed.add(assessment.activity_id)
        if final_check is not None:
            final_check["is_current"] = activity is not None and activity.activity_id in final_ids
            final_check["completed_count"] = len(final_ids & topic_completed)
            started = any(isinstance(event, AttemptStarted) and event.activity_id in final_ids
                          for event in self.events)
            final_check["status"] = (
                "completed" if final_ids.issubset(topic_completed)
                else "in_progress" if started else "not_started"
            )
        return {
            "status": state.status,
            "title": self.pack.title,
            "pack_id": self.pack.pack_id,
            "mode": self.mode,
            "session_id": state.session_id,
            "attempt_id": state.open_attempt_id,
            "phase": state.phase,
            "activity_id": None if activity is None else activity.activity_id,
            "activity_concept_id": None if activity is None else activity.concept_id,
            "question": question,
            "assessment_submitted": assessment is not None,
            "assessment_accepted": bool(assessment and assessment.payload.evaluation.accepted),
            "answer_feedback": answer_feedback,
            "experiment": experiment,
            "can_submit_response": (
                state.open_attempt_id is not None and state.phase == "awaiting_response"
                and (activity is None or activity.experiment is None or (
                    state.experiment_snapshot is not None
                    and experiment_ready_for_assessment(activity.experiment, state.experiment_snapshot)
                ))
            ),
            "workbench": (
                None if activity is None or activity.workbench is None
                else activity.workbench.model_dump(mode="json")
            ),
            "scenario_image": (
                None if activity is None else next(
                    (item.scenario_image.model_dump() if item.scenario_image is not None else None
                     for item in self.teaching_pack.activities if item.activity_id == activity.activity_id),
                    None,
                )
            ),
            "choices": choices,
            "causal_scene": scene_view,
            "turn": self._current_turn(state.current_activity_id),
            "conversation": self._conversation(),
            "pending_tutor_message": (
                None
                if pending_message is None
                else {
                    "request_id": pending_message.request_id,
                    "text": pending_message.payload.message.text,
                }
            ),
            "can_continue": (
                state.open_attempt_id is not None
                and state.completion_evidence_event_id is not None
            ),
            "can_send_message": (
                state.open_attempt_id is not None and state.phase == "awaiting_response"
            ),
            "learner_message_count": state.learner_message_count,
            "route_scope": state.route_scope,
            "preferred_activity_ids": state.preferred_activity_ids,
            "completed_activity_ids": state.completed_activity_ids,
            "final_check": final_check,
            "final_check_activity_ids": list(final_activity_ids),
            "completed_concept_ids": state.completed_concept_ids,
            "topic_practice_completed_concept_ids": tuple(
                concept.concept_id for concept in self.pack.concepts
                if (required := self.topic_activity_ids(concept.concept_id))
                and set(required).issubset(topic_completed)
            ),
            "m1_ready_concept_ids": state.m1_ready_concept_ids,
        }

    def developer_trace(self) -> dict[str, Any]:
        if not self.events:
            return {"events": [], "profile": None}
        event_rows: list[dict[str, Any]] = []
        for event in self.events:
            row: dict[str, Any] = {
                "sequence": event.sequence,
                "type": event.event_type,
                "activity_id": getattr(event, "activity_id", None),
            }
            if isinstance(event, ResponseRecorded):
                row["accepted"] = event.payload.evaluation.accepted
                row["misconception_id"] = event.payload.evaluation.misconception_id
            if isinstance(event, TeachingMoveSelected):
                row["strategy"] = event.payload.move.strategy
                row["selector_kind"] = event.payload.selector_kind
                row["fallback_reason"] = event.payload.fallback_reason
                row["interaction_focus_id"] = event.payload.interaction_focus_id
                row["dialogue_job"] = event.payload.dialogue_job
            event_rows.append(row)
        return {
            "events": event_rows,
            "profile": policy_learner_view(
                project_learner_profile(self.events)
            ).model_dump(mode="json"),
        }

    def _state(self):
        if not self.events:
            raise ValueError("start a demo session first")
        return replay(self.events)

    def _current_activity(self, activity_id: StableId | None):
        if activity_id is None:
            raise ValueError("the demo has no current activity")
        return next(
            activity
            for activity in self.pack.activities
            if activity.activity_id == activity_id
        )

    def _current_classification_response(
        self, attempt_id: StableId
    ) -> ResponseRecorded | None:
        return next(
            (
                event
                for event in reversed(self.events)
                if isinstance(event, ResponseRecorded)
                and event.attempt_id == attempt_id
                and isinstance(event.payload.evidence, ClassificationEvidence)
            ),
            None,
        )

    def _next_attempt_id(self, session_id: StableId) -> StableId:
        ordinal = 1 + sum(isinstance(event, AttemptStarted) for event in self.events)
        return f"{session_id}.attempt.{ordinal}"

    def _input_for_request(self, request_id: StableId):
        return next(
            (
                event
                for event in self.events
                if getattr(event, "request_id", None) == request_id
                and isinstance(
                    event,
                    (ResponseRecorded, SupportRequested, LearnerMessageRecorded),
                )
            ),
            None,
        )

    def _conversation(self) -> list[dict[str, Any]]:
        """Project the append-only trace into learner-visible chat messages."""

        messages: list[dict[str, Any]] = []
        example_roles: dict[StableId, AdjustmentExampleRoles] = {}
        for event in self.events:
            if isinstance(event, ResponseRecorded):
                messages.append(
                    {
                        "role": "learner",
                        "kind": "answer",
                        "activity_id": event.activity_id,
                        "attempt_id": event.attempt_id,
                        "concept_id": self._concept_id_for_activity(event.activity_id),
                        "text": self._choice_text(event),
                    }
                )
            elif isinstance(event, LearnerMessageRecorded):
                messages.append(
                    {
                        "role": "learner",
                        "kind": "message",
                        "activity_id": event.activity_id,
                        "attempt_id": event.attempt_id,
                        "concept_id": self._concept_id_for_activity(event.activity_id),
                        "text": event.payload.message.text,
                    }
                )
            elif isinstance(event, SupportRequested):
                if event.payload.request.kind == "orientation":
                    continue
                messages.append(
                    {
                        "role": "learner",
                        "kind": "support_request",
                        "activity_id": event.activity_id,
                        "attempt_id": event.attempt_id,
                        "concept_id": self._concept_id_for_activity(event.activity_id),
                        "text": "Please explain the distinction.",
                    }
                )
            elif isinstance(event, TeachingMoveSelected):
                if event.payload.move.strategy in {"advance", "hold"}:
                    continue
                messages.append(
                    {
                        "role": "tutor",
                        "kind": event.payload.move.strategy,
                        "activity_id": event.activity_id,
                        "attempt_id": event.attempt_id,
                        "concept_id": self._concept_id_for_activity(event.activity_id),
                        "references": (
                            self._references_for_move(event)
                            if event.payload.move.strategy == "direct_instruction"
                            else []
                        ),
                        "text": self._turn_for_event(event),
                    }
                )
                roles = example_roles_from_reply(event.payload.tutor_reply or "")
                if roles is not None and roles != example_roles.get(event.attempt_id):
                    messages[-1]["example_roles"] = roles.model_dump(mode="json")
                    example_roles[event.attempt_id] = roles
        return messages

    def _concept_id_for_activity(self, activity_id: StableId) -> StableId:
        return next(
            activity.concept_id
            for activity in self.pack.activities
            if activity.activity_id == activity_id
        )

    def _references_for_move(
        self, event: TeachingMoveSelected
    ) -> list[dict[str, str]]:
        """Expose only released claim/source metadata already validated by the runtime."""

        claims = {claim.claim_id: claim for claim in self.pack.claims}
        sources = {source.source_id: source for source in self.pack.sources}
        references: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for claim_id in event.payload.grounding_claim_ids:
            claim = claims.get(claim_id)
            if claim is None:
                continue
            for source_ref in claim.source_refs:
                source = sources.get(source_ref.source_id)
                if source is None:
                    continue
                key = (claim.claim_id, source.source_id, source_ref.locator)
                if key in seen:
                    continue
                seen.add(key)
                references.append(
                    {
                        "claim_id": claim.claim_id,
                        "proposition": claim.proposition,
                        "source_id": source.source_id,
                        "citation": source.citation,
                        "locator": source_ref.locator,
                    }
                )
        return references

    def _current_turn(self, activity_id: StableId | None) -> str | None:
        if activity_id is None:
            return None
        event = next(
            (
                item
                for item in reversed(self.events)
                if isinstance(item, TeachingMoveSelected)
                and item.activity_id == activity_id
            ),
            None,
        )
        if event is None:
            return None
        return self._turn_for_event(event)

    def _turn_for_event(self, event: TeachingMoveSelected) -> str:
        """Render a previously validated move with only released teaching wording."""

        payload = event.payload
        text = compose_tutor_turn(
            self.pack,
            ResolvedTutorTurn(
                activity_id=event.activity_id,
                candidate_id=payload.candidate_id,
                move=payload.move,
                framing_catalog_version=payload.framing_catalog_version,
                framing_id=payload.framing_id,
                grounding_resource_ids=payload.grounding_resource_ids,
                grounding_claim_ids=payload.grounding_claim_ids,
                expected_evidence_predicate_ids=(
                    payload.expected_evidence_predicate_ids
                ),
            ),
            socratic_question=payload.socratic_question,
            tutor_reply=payload.tutor_reply,
            allow_legacy_clarify=True,
        ).text
        # The exact stored header remains the replay/history anchor. Present its
        # roles once as structured message details, not as repeated machine prose.
        return text.split("\n", 1)[1] if example_roles_from_reply(text) is not None else text

    def _choice_text(self, event: ResponseRecorded) -> str:
        evidence = event.payload.evidence
        if isinstance(evidence, CausalSceneEvidence):
            return "Submitted the tested causal model and prediction."
        activity = self._current_activity(event.activity_id)
        option_id = _response_option_id(event)
        return next(
            choice.text for choice in activity.choices if choice.option_id == option_id
        )

    def _resource_text(self, resource_id: StableId) -> str:
        return next(
            resource.text
            for resource in self.pack.resources
            if resource.resource_id == resource_id
        )

    def _mutate(self, operation) -> None:
        start = len(self.events)
        operation()
        if self.store is not None:
            self.store.append(self.events[start:])


def _response_option_id(event: ResponseRecorded) -> StableId:
    evidence = event.payload.evidence
    if isinstance(evidence, ChoiceEvidence):
        return evidence.option_id
    if isinstance(evidence, ClassificationEvidence):
        return evidence.classification_id
    raise ValueError("causal-scene evidence has no option ID")


def _scene_focus_label(focus_id: StableId) -> str:
    return {
        "scene.open-records": "Open the observational records",
        "scene.propose-model": "Propose a causal model",
        "scene.elicit-prediction": "Make a prediction before the reveal",
        "scene.run-intervention": "Run the deliberate change",
        "scene.interpret-result": "Compare the result with your prediction",
        "scene.formal-evidence": "Consolidate your causal model",
    }[focus_id]
