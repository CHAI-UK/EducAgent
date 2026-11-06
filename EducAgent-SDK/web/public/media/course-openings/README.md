# M1 course-opening illustrations

Created 2026-10-15 using the built-in `image_gen` tool through the imagegen skill. Original generations were retained under the tool's generated_images directory; the selected PNGs are copied here for the project. No CLI/API fallback or new dependency was used.

## Files and intended use

- `effect-opening-v1.png`: fictional learning-support / rehabilitation planning scenes for both profiles' intervention opening.
- `shift-opening-v1.png`: fictional parcel inspection / hospital imaging scenes for both profiles' robustness opening.

These editorial images supply context only. They contain no assessment result, numerical evidence, clinical diagnosis or claim that a method works. Actual course results come from the scored runtime or declared experiment, never from these illustrations. Alt text and captions live in `content/course_introductions.json`. No external textbook figure was reproduced.

## Final prompts (verbatim)

### m1-effect-opening

```text
Use case: illustration-story. Asset type: landscape editorial illustration for the opening of a beginner causal learning course, Effect of an intervention. Primary request: illustrate the question of choosing a change, not merely predicting a record. A coherent two-scene spread: an adult community skills workshop comparing two training approaches, and a fictional physiotherapy clinic comparing two rehabilitation programmes. In each, a thoughtful instructor or clinician is planning a fair comparison with adult participants before taking action; show clipboards with abstract marks only. Warm approachable painted editorial style, clean human proportions, subtly textured gouache, restrained deep teal, sage, warm paper and muted terracotta consistent with an educational portal. Landscape 3:2 composition; scenes equally clear, a natural soft separation, no boxes, calm generous negative space, no large empty region reserved for text because text is outside this image. Scientifically careful: no proven improvement, no before-after miracle, no arrows implying discovered causation, no people receiving two treatments at once. No readable text, numbers, equations, labels, logos or watermark. No charts, no graph, no embedded UI. The illustration is fictional context, not evidence or a depiction of real study findings.
```

### m1-shift-opening

```text
Use case: illustration-story. Asset type: landscape editorial illustration for the opening of a beginner causal learning course, Robust prediction or generation. Primary request: illustrate a model meeting a different environment and the need to check what it relies on, not a claim of guaranteed robustness. A coherent two-scene spread: a parcel inspection workstation shows the same closed parcel photographed in bright indoor light and a dimmer warehouse setting; a fictional clinician compares abstract radiology images from two visibly different imaging rooms on two screens, with a short report sheet beside the source screen. All screens and paper contain abstract marks with no readable text, no scores, no diagnosis. People thoughtfully compare sources and context instead of declaring success. Warm approachable painted editorial style, clean human proportions, subtly textured gouache, restrained deep teal, sage, warm paper and muted terracotta matching an educational portal. Landscape 3:2 composition, two scenes equally clear with a natural soft separation and generous calm space; no boxes. Keep object identity the same across parcel views; only surrounding context and lighting differ. No inferred biological treatment changes, no causal arrows, no graph, no accuracy claims, no numbers, no labels, no logos, no watermark, no embedded UI. This is fictional teaching context, not clinical evidence.
```
