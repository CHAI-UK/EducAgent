"""Render hypothetical adjustment examples from one explicit role assignment.

This is an internal reply format, not a scientific claim, assessment contract,
or semantic checker for arbitrary prose. The model can propose short role labels;
it cannot independently choose a different variable for grouping or weighting.
"""

import re
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from .contracts import ContractModel
from .turns import MAX_TUTOR_REPLY_CHARS


RoleLabel = Annotated[str, StringConstraints(
    strip_whitespace=True, min_length=1, max_length=75, pattern=r"^[^;=\n\r|]+$",
)]


def _role_key(label: str) -> str:
    return re.sub(r"\W+", " ", label.casefold()).strip()


class AdjustmentExampleRoles(ContractModel):
    treatment: RoleLabel
    outcome: RoleLabel
    common_cause: RoleLabel
    target_population: RoleLabel

    @model_validator(mode="after")
    def distinct_causal_roles(self) -> Self:
        labels = [_role_key(label) for label in (
            self.treatment, self.outcome, self.common_cause,
        )]
        if len(set(labels)) != 3:
            raise ValueError("treatment, outcome and pre-treatment common cause must be distinct variables")
        return self


class AdjustmentExampleReply(ContractModel):
    """A worked analogy: choose roles and a step, never free-write its causal clauses."""

    roles: AdjustmentExampleRoles
    focus: Literal[
        "roles", "compare", "simple", "timing", "standardize", "assumptions", "clarify", "correction", "question",
    ] = Field(description=(
        "roles introduces the example; compare explains within-group comparison; "
        "simple gives short steps; timing distinguishes baseline and outcome; "
        "standardize explains common target weights; assumptions states identification limits; "
        "clarify distinguishes a newly mentioned variable; correction repairs an actual "
        "previous role substitution; question asks one Socratic question."
    ))
    extra_variable: RoleLabel | None = None
    introduce_new_example: bool = False


_ROLE_HEADER = re.compile(
    r"^Example roles: treatment = ([^;\n]+); outcome = ([^;\n]+); "
    r"pre-treatment common cause = ([^;\n]+); target population = ([^\n]+)\n"
)


def example_roles_from_reply(text: str) -> AdjustmentExampleRoles | None:
    """Recover only our exact rendered header, not inferred roles from old prose."""

    match = _ROLE_HEADER.match(text)
    if match is None:
        return None
    try:
        return AdjustmentExampleRoles(**dict(zip(
            ("treatment", "outcome", "common_cause", "target_population"),
            match.groups(), strict=True,
        )))
    except ValueError:
        return None


def render_adjustment_example(plan: AdjustmentExampleReply) -> str:
    """Keep full replayable roles; use explicit aliases if their repetition is too long."""

    r = plan.roles
    header = (
        f"Example roles: treatment = {r.treatment}; outcome = {r.outcome}; "
        f"pre-treatment common cause = {r.common_cause}; target population = {r.target_population}\n"
    )
    prefix = "Switching explicitly to a new hypothetical example: " if plan.introduce_new_example else ""
    text = header + prefix + _render_adjustment_body(plan, r)
    if len(text) <= MAX_TUTOR_REPLY_CHARS:
        return text
    aliases = AdjustmentExampleRoles(
        treatment="the treatment", outcome="the outcome",
        common_cause="the starting condition", target_population="the target population",
    )
    return (header + prefix + "Using these roles, with starting condition meaning common cause: "
            + _render_adjustment_body(plan, aliases, compact=True))


def _render_adjustment_body(
    plan: AdjustmentExampleReply, r: AdjustmentExampleRoles, *, compact: bool = False,
) -> str:
    """The same teaching premises apply to full labels and their compact role aliases."""

    strategies = "treatment strategies" if compact else f"{r.treatment} strategies"
    group = "starting-condition" if compact else r.common_cause
    assumption = (
        f"In this hypothetical example, suppose {r.common_cause} is measured before treatment "
        f"and affects both {r.treatment} and {r.outcome}. "
    )
    compare = (
        f"Compare {r.outcome} under the alternative {strategies} within each "
        f"{group} group, rather than mixing unlike starting groups. "
    )
    standardize = (
        f"Then combine these within-{group} comparisons using the same "
        f"{group} distribution in {r.target_population} for both strategies. "
    )
    limits = (
        f"This estimates a causal effect only if adjusting for {r.common_cause} removes "
        "confounding, both strategies are possible in each relevant group, and the "
        "treatment and outcome have consistent meanings. These are assumptions, not facts proved by grouping."
    )
    if plan.focus == "roles":
        body = assumption + compare
    elif plan.focus == "compare":
        body = assumption + compare + standardize
    elif plan.focus == "simple":
        body = (
            f"Take one {group} group at a time. Within that group, compare "
            f"{r.outcome} under the alternative {strategies}. "
            f"Repeat for the other {group} groups, then give both strategies "
            f"the same group mix in {r.target_population}. Grouping alone does not prove causality."
        )
    elif plan.focus == "timing":
        body = (
            f"{r.common_cause} is a starting condition in this hypothetical example, "
            f"not a consequence of {r.treatment}. We compare similar starting groups "
            "to address pre-existing differences in treatment choice. "
            f"{r.outcome} is the outcome we want to compare, not a replacement adjustment "
            "variable. Conditioning on a treatment consequence can remove part of the "
            "effect or introduce bias; being measured before treatment is necessary "
            "for this common-cause role but does not by itself make an adjustment set sufficient."
        )
    elif plan.focus == "standardize":
        body = (
            standardize + "Otherwise the contrast can reflect different starting-group "
            "mixtures as well as treatment differences. " + limits
        )
    elif plan.focus == "question":
        body = (
            f"If the groups receiving different {strategies} have different "
            f"{group} mixtures, what might their overall difference in "
            f"{r.outcome} reflect besides a treatment effect?"
        )
    elif plan.focus == "assumptions":
        body = assumption + limits
    elif plan.focus == "clarify":
        other = plan.extra_variable or "A newly mentioned variable"
        if plan.extra_variable is not None and _role_key(other) == _role_key(plan.roles.common_cause):
            body = (
                f"That names the existing starting condition, {r.common_cause}, not a different variable. "
                "Its common-cause role is a hypothetical assumption; measuring it before treatment "
                "does not by itself establish adequate confounding control. " + compare
            )
        else:
            body = (
                f"{other} is not automatically the same variable as {r.common_cause}. "
                f"Our example assigns the common-cause role to {r.common_cause}; do not silently "
                "replace it with another grouping variable. A further cause could require a revised "
                "causal model and adjustment set, not just a change of names. " + compare
            )
    else:
        body = (
            "If my earlier wording changed variables, that was inconsistent. "
            f"Keep {r.common_cause} as the pre-treatment common cause in this example. "
            + compare + standardize
        )
    return body
