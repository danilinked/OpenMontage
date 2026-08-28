---
name: camera-movements
description: |
  Reference taxonomy of camera movement types (pan, tilt, dolly, truck, pedestal,
  zoom, crane, orbit, handheld, etc.) and how to phrase them in natural-language
  prompts for AI video generators (Kling, Veo, MiniMax, Seedance). Use when: (1)
  Writing or improving image-to-video / text-to-video prompts that need camera
  direction, (2) Choosing a camera movement for a shot's mood or purpose, (3)
  Deciding whether a movement is likely to render cleanly vs. fall apart in
  current AI video models, (4) Picking a go-to camera move for a common content
  type (product B-roll, lifestyle/outdoor, establishing shot, close-up detail).
  Source: distilled from aicameramovements.com.
metadata:
  openclaw:
    source: https://aicameramovements.com/
---

# Camera Movements (Layer 3 — Vendor/Technology Knowledge)

This is raw camera-movement knowledge, independent of any single provider. It
complements `ai-video-gen` (which covers the generation API/tool call itself)
and `seedance-2-0` (which covers that model's director-level camera control).
Read this skill when the task is *writing the camera-movement part of the
prompt*, regardless of which provider ends up generating the clip.

## Reference Table

| Movement | Physical description | Mood / effect | Example prompt phrasing |
|---|---|---|---|
| Pan right / left | Rotate camera horizontally from one fixed point | Exploratory reveal of adjacent space | "pan right", "pan left" |
| Whip pan right / left | Rapid rotation toward a new target | High-energy, jarring subject-to-subject transition, motion blur | "whip pan right" |
| Tilt up | Rotate camera upward from a fixed point | Reveals vertical scale, grandeur, ascension | "tilt up" |
| Tilt down | Rotate camera downward from a fixed point | Descending perspective, reveals ground-level detail | "tilt down" |
| Slow zoom in | Lens focal length gradually tightens | Subtle intensification, gradual attention-draw | "slow zoom in" |
| Slow zoom out | Lens focal length gradually widens | Gradual context reveal, establishing relationships | "slow zoom out" |
| Fast / crash zoom in | Lens snaps rapidly toward subject | Emphatic, punchy, dramatic or comedic punctuation | "crash zoom in" |
| Fast / crash zoom out | Lens snaps rapidly away from subject | Bold scale shift, jarring perspective change | "crash zoom out" |
| Dolly in | Camera physically moves forward toward subject | Intimate intensification; preserves parallax (unlike zoom) | "dolly in" |
| Dolly out | Camera physically moves backward away from subject | Contextual expansion, reveals environment | "dolly out" |
| Tracking shot | Camera moves through the scene with the subject | Maintains subject relationship while traversing space | "tracking shot" |
| Follow shot (over-the-shoulder) | Camera moves behind subject at shoulder height | Intimate, "in on the action" follower perspective | "follow shot from behind" |
| Reverse tracking (walk-and-talk) | Camera moves backward in front of a walking subject | Conversational, face-forward engagement | "reverse tracking shot" |
| Side tracking | Camera moves parallel beside the subject | Profile perspective, parallel motion emphasis | "side tracking shot" |
| Low tracking | Camera moves at ground/below-waist height alongside subject | Ground-level, detail-emphasizing perspective | "low tracking shot" |
| Chase shot | Camera follows a fast-moving subject closely | High energy, pursuit / urgency | "chase shot" |
| Truck right / left | Camera moves laterally on a straight horizontal path | Sideways environment reveal | "truck right", "truck left" |
| Pedestal up / down | Whole camera rises or lowers vertically, straight line | Ascending/descending reveal without tilt | "pedestal up", "pedestal down" |
| Slider right / left | Small lateral slide | Subtle parallax, refined compositional shift | "slider right" |
| Push past / pass-by | Camera moves forward past a foreground object or opening | Threshold-crossing, "arrival" sensation | "push past the doorway" |
| Arc right / left | Camera moves on a shallow curved path around subject | Angular repositioning, mild orbital reveal | "arc left around the subject" |
| Orbit (clockwise / counterclockwise) | Camera circles subject at constant radius, subject stays centered | 360° environmental reveal, showcase framing | "clockwise orbit around the subject" |
| Crane up / down | Smooth vertical travel through open space (boom arm) | Aerial ascent/descent, scale expansion | "crane up", "crane down" |
| Drone push in / pull back | Aerial forward/backward flight toward or away from subject | Approach or retreat from above, epic scale | "drone push in toward the campsite" |
| Helicopter shot | High-altitude camera on a broad, gradual flight path | Expansive landscape survey | "helicopter-style aerial shot" |
| Handheld | Camera at operator height with natural body sway | Documentary authenticity, intimacy, subtle imperfection | "handheld shot with subtle sway" |
| Body-mounted (Snorricam) | Camera rigidly fixed relative to subject's torso/face | Subject locked in frame, background swims — surreal/disorienting | "body-mounted Snorricam shot" |
| Static / locked-off | One fixed camera position for the whole clip | Stability, compositional focus, calm | "locked-off static shot" |
| First-person view | Camera moves at eye height from character's POV | Subjective immersion | "first-person point-of-view shot" |
| Tilt-shift | High angled view with narrow sharp band, rest blurred | Miniaturization / diorama effect | "tilt-shift miniature look" |
| Infinite zoom | Continuous accelerating zoom toward a center target | Endless-depth, portal sensation | "infinite zoom toward the center" |
| Earth zoom out | Pulls up through street → city → landscape → planet scale | Cosmic scale reveal | "earth zoom out from the campsite to orbit" |
| Time-lapse | Fixed camera, time compressed | Passage-of-time, process visualization | "locked-camera time-lapse" |

## Combining Movement with Scene Description

Kling, Veo, MiniMax, and Seedance all take a single text prompt with no
separate "camera" field (Seedance 2.0's director-mode controls are the
exception — see `seedance-2-0`), so the movement instruction has to live
inside the same sentence as the subject/scene description. The source
material's core principle is **separation of concerns within one string**:
keep the camera instruction and the scene idea as distinct clauses so either
can be swapped independently when iterating.

A reliable structure:

```
[camera movement] + [subject/action] + [setting/environment] + [lighting/mood] + [style qualifiers]
```

Example:
> "Slow dolly in on a family unpacking a tent at a forest campsite, golden
> hour light filtering through pine trees, warm and inviting, cinematic
> travel-documentary look."

Guidance from the source and general practice:
- Name the movement explicitly and put it first or right after any opening
  shot-type word ("wide shot, slow zoom out on...") — models weight early
  tokens more heavily for global motion.
- Add a speed/intensity descriptor (`slow`, `slight`, `fast`, `subtle`) —
  unqualified movement words are the single biggest source of over-animated,
  unstable output.
- Add an ending-composition cue when it matters ("...ending on a close-up of
  their hands tying the knot") — this reads as a target for interpolation
  rather than a free-running motion.
- Repeat consistency language the source emphasizes: "smooth," "controlled,"
  "steady," "readable" — these keywords bias models toward coherent single
  moves instead of drifting compound motion.
- Keep the whole prompt reusable: write the camera clause so it survives a
  swap of the first-frame image (i.e., don't bake image-specific details into
  the movement clause itself).

## What Renders Well vs. Poorly (current AI video models, 2025-2026 generation)

- **Renders reliably:** single, simple moves — slow dolly in/out, pan,
  handheld sway, static shot, slow zoom, pedestal up/down. Subtlety is an
  asset: a small, well-described move looks intentional; an unqualified large
  move often produces warping, especially at the frame edges or with complex
  foreground occlusion.
- **Renders inconsistently:** orbit/arc shots (constant-radius circling)
  often drift off-radius or lose subject lock over more than ~2-3 seconds;
  crane/drone moves can produce floaty, physically implausible acceleration;
  whip pans and crash zooms frequently introduce artifacting during the fast
  segment even though the concept itself is simple.
- **Renders poorly / avoid stacking:** compound moves in one prompt (e.g.,
  "dolly in while orbiting and tilting up") — current models tend to average
  or drop one of the motions rather than executing all simultaneously. Prefer
  one dominant movement per shot; if a compound feel is needed, cut two clips
  instead of asking for one shot to do both.
- **Image-to-video specific (Kling and similar):** movements that would
  require inventing content outside the source photo's frame (e.g., "orbit
  fully around" a subject only shown from one angle) frequently hallucinate
  or distort the unseen side. Prefer moves that stay within or push toward
  what's plausibly inferable from the still (push in, subtle pan, handheld
  sway) over moves that demand new geometry (full orbit, big reveal pans).

## Quick Picks — Go-To Prompts by Content Type

- **Product B-roll:** "Slow, controlled dolly in on [product] resting on
  [surface], soft studio lighting, shallow depth of field, ending close on
  the product label." — subtle push-in reads as premium and renders cleanly.
- **Lifestyle / outdoor scene:** "Handheld shot with subtle natural sway
  following [subject] walking through [outdoor setting], warm golden-hour
  light, documentary travel-video feel." — handheld sway hides small
  generation artifacts and reads as authentic.
- **Establishing shot:** "Slow zoom out revealing [location] in full, wide
  framing, soft haze in the distance, calm and expansive mood." — zoom-out
  establishing shots are one of the most reliable wide-context moves.
- **Close-up detail shot:** "Static locked-off shot, slight rack-focus pull
  onto [detail], soft shallow depth of field, quiet and intimate." — favor
  near-static framing for detail shots; motion competes with the detail
  itself.
- **Campsite / gear reveal (this project's use case):** "Slow pedestal up
  from the tent stakes to the full tent silhouette against the treeline,
  early morning light, calm and grounded feel." — vertical reveal works well
  on single still photos where a full orbit would need to invent hidden
  sides.

## Source

Distilled from https://aicameramovements.com/ (movement taxonomy, phrasing
conventions, and the "separate the camera clause from the scene clause"
prompting principle). Reliability notes (what renders well/poorly) reflect
general current-model behavior as of this writing, not claims made by the
source site — validate against the specific provider (`ai-video-gen`,
`seedance-2-0`) before relying on them for a shot that must land on the first
generation.
