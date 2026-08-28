# Intro/Outro House Style (reference: "Bandolera Versox" promo)

> Source: https://www.youtube.com/watch?v=EyyfGGj9KF4 (74s, silent/music-only,
> analyzed via `video_analyzer` deep mode). User's own prior work — adapt, don't
> copy verbatim. Use this as the default intro/outro treatment whenever a video
> doesn't already have one specified.

## When to Use

Apply this pattern whenever a production brief needs a polished intro and/or
outro and no other reference is given. Works for both landscape (16:9) and
vertical (9:16) — the layout logic is safe-zone based, not orientation-locked.

## 5-Aspect Breakdown

**Subject:** N/A for intro/outro cards — pure typography/UI, no live subject.
Body sections show the product as subject (still or floating/rotating).

**Subject Motion:** N/A for text cards. Product shots use subtle floating/rotation.

**Scene:**
- Overlays: bold title + thin underline + subtitle (intro); left-aligned
  headline + contact/detail list + device mockup (outro). No lower-thirds.
- POV: locked-off, no camera movement (this is a graphics-only sequence).
- Setting: pure color backgrounds (black for intro/transitions, light neutral
  gray for outro) — no photographic environment.
- Dynamics: none; all motion comes from typography animation and wipes.

**Spatial Framing:** Intro/outro text is a full-frame centered (intro) or
left-third-anchored (outro) block. Product-reveal body scenes split the frame
left/right (~35/65).

**Camera:** Static/locked throughout — all movement is in the 2D graphics layer
(spring pop-ins, wipes), never simulated camera motion.

## Intro Pattern (~3-5s)

1. Brief fade-in from a light/particle frame (~0.3-0.5s) — optional, skip if
   tight on time budget.
2. Cut to solid black background.
3. Bold title, white, centered, large (72-90px at 1080p), letter/word stagger-in.
4. Thin horizontal accent-color underline animates width in under the title.
5. Subtitle below in a muted/desaturated tone, smaller, uppercase, letter-spaced.
6. Hold 2-3s, then transition into body content.

**Maps directly to `HeroTitle` (already in `remotion-composer/src/components/HeroTitle.tsx`)** —
`title`, `subtitle`, `accentColor` (underline + first-word highlight),
`textColor`, `subtitleColor` props already support this. No new component needed
for the intro card itself.

```json
{
  "id": "intro",
  "type": "hero_title",
  "in_seconds": 0,
  "out_seconds": 4,
  "text": "BIENVENIDO",
  "subtitle": "a [tagline de marca]",
  "accentColor": "#137C61",
  "color": "#FFFFFF",
  "subtitleColor": "#D7F2EA",
  "backgroundColor": "#000000"
}
```

## Body: Product-Reveal Split Card

Left panel (dark) holds a bordered box with product name + reference/detail
line; right panel (light) shows the product photo, floating or slowly rotating.

**Maps to the existing `ProductReveal` / `ProductRevealVertical` compositions**
(`remotion-composer/src/Root.tsx`) — `productImage`, `productName`, `tagline`,
`accentColor` already cover this shape. Use `ProductRevealVertical` for 9:16 ads.

## Transitions

- Between sections: short (1-2 word) text beats appearing on black,
  word-by-word — same stagger mechanic as the intro title, just shorter and
  without the underline/subtitle.
- Scene changes: circular/radial wipe (iris transition) rather than a hard cut
  or simple crossfade — reads as more "produced."

## Outro Pattern (~5-8s)

1. Light neutral background (off-white/gray, NOT the dark intro tone — outro
   deliberately flips brightness to signal "wrap-up").
2. Small logo/wordmark top-left corner, low-key, not the hero element.
3. Big bold headline, LEFT-ALIGNED (not centered) — CTA statement
   ("Cómpralo ahora", "Escríbenos", "Disponible ya").
4. Below the headline: a short supporting list (contact info, availability,
   guarantee line) in regular weight, smaller size, same left alignment.
5. Optional right-side visual: device mockup, product shot, or the brand mark
   at larger scale — balances the left-heavy text block.
6. Close on a circular/radial wipe (mirrors the intro's opening logic) —
   optionally revealing the brand mark full-frame as the very last beat.

**Maps to the `EditorialScene` component** (`remotion-composer/src/components/EditorialScene.tsx`,
built during the MuchoCamping ad session) — it already has the white card,
kicker, left-aligned bold headline, and accent bar. For the outro specifically:
drop the `stat` card, use `kicker` for a one-line supporting detail, and pair
with the `brandMark` prop (already on `ExplainerProps`) instead of a raster logo.

```json
{
  "id": "outro",
  "type": "editorial",
  "in_seconds": 26,
  "out_seconds": 30,
  "kicker": "DISPONIBLE YA",
  "text": "Escríbenos y lo tienes en tu próxima ruta",
  "accentColor": "#137C61",
  "backgroundImage": "<product or lifestyle still>",
  "backgroundOverlay": 0.4,
  "backgroundOverlayColor": "15,46,39"
}
```
Plus top-level `"brandMark": { "color": "#137C61", "accentColor": "#F1DD30", "position": "bottom-right" }`
already covers the logo requirement without needing the low-res raster file.

## Quick Checklist When Applying This House Style

- [ ] Intro: `hero_title` cut, black bg, 3-4s, brand accent underline
- [ ] Body: `ProductRevealVertical` or `editorial` cuts for product beats
- [ ] Transitions: short word-stagger text beats or circular wipe between scenes
- [ ] Outro: `editorial` cut, light bg, left-aligned CTA headline + short detail
      line, `brandMark` overlay instead of a logo image
- [ ] Keep total intro+outro budget to ~8-10s combined on a 30s social cut —
      don't let it eat into the 20s of actual product content (see
      `skills/creative/short-form.md` pacing rules)
