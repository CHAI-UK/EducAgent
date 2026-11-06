# Foundation lesson sample illustrations

These AI-generated PNGs were created with the imagegen tool for the first-stage
General/Medical `association-is-not-causation` sample. They are fictional scenario
context, not photographs of identified people, observations, treatment results,
textbook figures or evaluator inputs. The sample text and accessibility labels
are authored in `content/foundation_lesson_samples.json`; its causal content
remains pending expert review.

| File | Context and use |
| --- | --- |
| `general-association.png` | A sunny fictional seaside promenade, an ice-cream stall and people outdoors. It introduces the recorded-pattern example without depicting a causal conclusion. |
| `medical-association.png` | A fictional clinic with a clinician, a seated patient and another waiting patient. It introduces treatment receipt/recovery as possible recorded variables without asserting a treatment effect. |

The following prompt directions are reconstructed from the authoring brief and
the resulting illustrations. They are not a preserved verbatim generation log;
no model/version, seed or literal tool prompt is asserted here.

## General illustration: reconstructed prompt direction

Create a horizontal, softly rendered editorial illustration of a sunny seaside
town. Show an ice-cream stall beside a promenade with ordinary adults spending
time outdoors. Use warm daylight, muted teal and cream details, and a calm,
legible composition suitable for a beginner learning page. Show neutral context
only: no visibly diagnosed sunburn, statistical chart, causal arrows, answer
labels, text instructions or claim that ice cream causes a health outcome.

## Medical illustration: reconstructed prompt direction

Create a horizontal illustration in the same restrained style and palette,
showing a calm fictional clinic. Include a clinician discussing a plain clipboard
with a seated adult patient and another patient waiting nearby. Preserve privacy
through fictional, generic surroundings and no readable patient records. Do not
show a named real treatment, recovery result, causal arrows, answer labels,
statistical chart or an implied comparison that demonstrates benefit or harm.

## Diagram and evidence boundary

The worked common-cause diagram is not part of either PNG. The browser draws it
from the released lesson's typed `worked_graph` nodes and edges and includes its
"possible explanation" label and note. That graph is an authored hypothesis,
not a conclusion identified from the fictional records. Scoring uses declared
activity choices and SDK evaluators, never image recognition or visual details.
The typed worked-graph contract accepts only the current three-node, two-edge
common-cause fork so unsupported graphs cannot be rendered as this layout.

Keep this provenance file with the canonical source assets. A public release
should retain the synthetic-example labels and alt text; it must not attribute
these illustrations to the textbook or describe them as causal-expert approval.

## S32 park illustration anatomy correction (2026-10-19)

The adjacent `media/causality-m0/observed-association-park-v2.png` is a
versioned imagegen edit of `observed-association-park.png`. It corrects the
cream-shirt woman's arms only; the original remains available to historical
content packs. The result was visually inspected before use. It provides
fictional scene context, not observations or evidence of an exercise effect.
The built-in imagegen tool was used with the following exact prompt:

> Use case: precise-object-edit. Asset type: educational illustration in an adult causal-reasoning course. Image 1 is the edit target. Fix ONLY the anatomy and pose of the white/cream-shirt woman standing immediately to the right of the blue-shirt man. Her arms currently look unnaturally stretched and tangled across her chest/shoulder. Give her exactly two anatomically plausible arms with natural shoulder connections, elbows and hands, relaxed comfortably at her sides with a little separation from her torso. No stretching pose, crossed arms or contact with adjacent people. Preserve her head, face, body proportions, cream shirt, slate-blue trousers and position. Preserve every other person, the tablet, exercise park, palette, soft painterly texture, lighting, composition and square framing. Do not add labels, charts, text or new props. This image provides scene context only, not evidence of a medical finding. The edit should look like the same original illustration with only the troublesome arms corrected.
