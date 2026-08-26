# Prompt structure rules

Defines how a video generation prompt is structured, per video type, and the
rules used to evaluate and improve one. The full machine-readable version of
this is `rules.json`; this document explains what it means.

## Shared fields

Every video type is built from these fields:

| Field             | Rule                                                                                  |
|--------------------|----------------------------------------------------------------------------------------|
| `subject`          | Concrete, visually groundable description of who/what is the focus. No abstract adjectives with no visual referent. |
| `action`           | What happens over the clip. Must be achievable within a short clip — a single continuous motion, not a multi-beat sequence. |
| `scene`            | Environment, background, time of day — specific enough to anchor lighting and mood.   |
| `camera`           | Shot type and movement. Must be physically compatible with the described action.      |
| `lighting`         | Lighting style/mood. Must not contradict the scene's implied conditions.               |
| `style`            | A concrete visual/style reference (rendering style, film stock, animation technique) — never a vague quality adjective like "high quality". |
| `negative_prompt`  | Concrete failure modes to avoid for this content type, not generic boilerplate.        |

## Video types

Each video type reuses the shared fields and, where its content genuinely
requires it, adds fields of its own. Types that only differ in tone/vocabulary
share the same field set; a new field is only added when the shared fields
can't express something that type needs.

| Video type | Extra fields | What distinguishes it |
|---|---|---|
| `pixar` | — | 3D animated feature conventions: stylized proportions, warm rim lighting, readable motion. |
| `action` | — | Kinetic camera language, impact-driven pacing. |
| `animation` | — | Generic animation; must name a concrete technique (2D cel-shaded, stop-motion, cutout). |
| `anime` | — | Anime-specific conventions: cel-shading, speed lines, dramatic zoom, exaggerated expression. |
| `documentary` | — | Observational, photorealistic camera language; avoids stylized moves that break realism. |
| `fashion` | — | Wardrobe/material detail, editorial lighting (studio strobe, natural window light). |
| `ugc_product_review` | `dialogue`, `reference_image` | Handheld/amateur/phone-camera tone. `reference_image` anchors exact product appearance. |
| `commercial_product_ad` | `dialogue`, `reference_image` | Same fields as UGC, opposite tone: polished studio lighting, smooth camera moves. |
| `explainer_testimonial` | `dialogue`, `reference_image` | Clear, well-lit, direct-to-camera; dialogue is informative/persuasive, not casual. |
| `presenter_avatar` | `dialogue`, `reference_image`, `voice_tone` | A recurring speaker. `reference_image` anchors identity across separate generations; `voice_tone` directs how the speech should sound. |
| `social_short_form_ad` | `dialogue`, `reference_image`, `text_overlay`, `aspect_ratio` | Fast, hook-driven, vertical framing; `text_overlay` is on-screen captions, `aspect_ratio` defaults to `9:16`. |
| `music_video` | `audio_reference`, `tempo_bpm` | Rhythm/beat-synced visuals rather than narrative action. Not supported by any currently integrated model — defined for future use. |
| `motion_graphics` | `text_content`, `transitions` | Abstract/graphic style (flat design, iconography, kinetic typography) rather than photoreal/cinematic. Better served by templated motion-graphics tooling than diffusion video models today. |

## Evaluation criteria

Each video type carries a list of criteria a prompt is checked against, on
top of the criteria shared by every type (specificity, camera/action
consistency, lighting/scene consistency, negative-prompt coverage, duration
feasibility, and all required fields being non-empty). Each criterion has:

- **`check_type`** — `structural` if it can be computed deterministically
  from the prompt/params (field presence, length, enum membership,
  word-count-vs-duration math), or `semantic` if it requires judgment (tone,
  physical plausibility) via an LLM-as-judge pass.
- **`severity`** — `blocking` if the prompt should not go to generation until
  it passes (always a `structural` check with an unambiguous failure
  condition), or `quality` if it contributes to a score without stopping
  generation.
- **`weight`** — relative importance (0–1) among the `quality` criteria in
  the same scope, for computing an aggregate score. Not set for `blocking`
  criteria, since those gate rather than score.
- **`remediation`** — the concrete fix to try when the criterion fails,
  phrased as a field update rather than just a description of the problem.

Some recurring blocking checks worth calling out explicitly:

- **`dialogue_duration_fit`** — spoken word count, at ~2.5 words/second,
  must fit the requested clip duration. Applies to every dialogue-bearing
  type.
- **`caption_length_fit` / `text_length_fit`** — on-screen text character
  count, at ~15 readable characters/second, must fit the clip duration.
  Applies to `social_short_form_ad` and `motion_graphics`.
- **`audio_reference_present`** — `music_video` cannot be evaluated at all
  without a reference track to sync to.
- **`aspect_ratio_valid`** — `social_short_form_ad` must use a known
  vertical short-form ratio (`9:16`, `4:5`).

This ruleset is the data contract a future prompt evaluator/improver will
read against: given a video type and a compiled prompt, it resolves that
type's criteria, scores or blocks the prompt accordingly, and applies each
failing criterion's `remediation` until the prompt clears an acceptable
threshold.
