"""Teach the complementary Shift challenge facets in the visible lesson core.

The existing assessment pairs already test different facets. Keep every
question and experiment, expand three worked examples and align one lesson
title with its example. The caller assigns the release version and leaves
historical packs untouched.
"""

if __package__:
    from .m1_shift_revision import CONCEPT_IDS
else:
    from m1_shift_revision import CONCEPT_IDS


def apply_shift_challenge_revision(data: dict, profile: str) -> None:
    """Update visible worked examples in place without changing assessments."""
    if profile not in {"general", "medical"}:
        raise ValueError("shift challenge revision requires general or medical")
    if data.get("pack_id") != f"causality.m1.shift.{profile}":
        raise ValueError("shift challenge revision requires the matching shift profile pack")
    if tuple(item["concept_id"] for item in data["concepts"]) != CONCEPT_IDS:
        raise ValueError("shift challenge revision requires the existing four-concept curriculum")
    if len(data["activities"]) != 16:
        raise ValueError("shift challenge revision requires the existing sixteen activities")

    medical = profile == "medical"
    examples = {
        CONCEPT_IDS[0]: (
            "A hospital wants an assistant to predict whether an opacity is present on a chest image. "
            "An opacity is a cloudy area, not a diagnosis by itself. The assistant can read a hospital "
            "marker or a recorded opacity flag, a yes/no image finding. At the first hospital, the marker "
            "often matches the checking answer. At another hospital, the marker is applied differently "
            "and image findings are recorded less reliably. A separate test there checks the proposed "
            "use. If accuracy is lower, the scores alone "
            "cannot separate the effects of those changes."
            if medical else
            "A warehouse assistant predicts whether a parcel is damaged. It can read a warehouse label "
            "or a recorded parcel-damage flag, a yes/no finding from a photograph. At the first warehouse, "
            "the label often matches the checking answer. Suppose another warehouse uses its labels "
            "differently and records photograph findings less reliably. A separate test there checks the proposed "
            "use. If accuracy is lower, the scores alone cannot separate the effects of those changes."
        ),
        CONCEPT_IDS[2]: (
            "Two hospitals report the same overall accuracy for opacity predictions, but one sees a "
            "larger share of older adults. Compare errors for similar younger adults across hospitals, "
            "then compare similar older adults. Different group sizes can hide a change within a group. "
            "This compares errors; it does not by itself establish that the same measured features have "
            "the same outcome patterns, prove a cause or cover untested kinds of patients."
            if medical else
            "Two warehouses report the same overall accuracy for parcel-damage predictions, but one "
            "handles a larger share of large parcels. Compare errors for similar small parcels across "
            "warehouses, then compare similar large parcels. Different group sizes can hide a change "
            "within a group. This compares errors; it does not by itself establish that the same measured "
            "features have the same outcome patterns, prove a cause or cover untested kinds of parcels."
        ),
        CONCEPT_IDS[3]: (
            "So far the assistant has predicted whether an opacity is present, a cloudy area on a chest "
            "image. It now writes a report. Suppose the report needs the scan date, but the source gives "
            "only the image finding and no date. The assistant can retain that finding, mark the date "
            "as unavailable and leave the incomplete report for review. Making up a date would add a "
            "fact without evidence. This response does not verify the missing information. A new "
            "recording setup still needs its own evaluation."
            if medical else
            "So far the assistant has predicted whether a parcel is damaged. It now writes a report. "
            "Suppose the report needs the inspection date, but the source gives only the damage finding "
            "and no date. The assistant can retain that finding, mark the date as unavailable and leave "
            "the incomplete report for review. Making up a date would add a fact without evidence. "
            "This response does not verify the missing information. A new recording setup still needs "
            "its own evaluation."
        ),
    }
    resources = {item["resource_id"]: item for item in data["resources"]}
    lessons = {item["concept_id"]: item for item in data["lessons"]}
    for concept_id, text in examples.items():
        resources[lessons[concept_id]["hook_resource_id"]]["text"] = text
    lessons[CONCEPT_IDS[2]]["title"] = "Check stability across settings"
