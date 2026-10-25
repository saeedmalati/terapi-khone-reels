# Style catalog — never repeat the previous 3 pieces

Every piece records its choices in log.json under "style": {font, layout, reveal, title, palette, footage_id}.
Before building, read the last 3 entries and choose a combination that differs in at least
font OR layout, AND in reveal AND in footage. Invent new variations too; this list is a floor, not a ceiling.

## Fonts (handwritten / calligraphic, all in template/reel-video/assets/fonts)
- Nastaliq (Noto Nastaliq Urdu 400/700) — most elegant; default for deep emotional lines
- Gulzar 400 — softer Nastaliq
- Ruqaa (Aref Ruqaa 400/700) — quick handwritten-pen feel
- Latin watermark only: VazLatin

## Layouts (all text between y=168 and y=1330, centered horizontally unless stated)
1. Title on top + one sentence at a time in the middle (reel «رفیق»)
2. No title; each sentence big, centered, one per beat
3. Lines accumulate: each new line is written under the previous ones, the whole block fades at the end
4. Lower block: text in the band y≈900–1250 over a dark gradient, title small above it
5. Right-aligned poem block (text-align: right, right padding 90px), like handwritten notes
6. One key word huge (e.g. «مادر») stays; short lines change around it
7. Two-voice: question line top, answer line bottom
8. Final end-card: last line alone, larger, centered, held 2–3 s

## Reveals (keep RTL; never split Persian words into letters)
- Right-to-left pen mask (soft edge), per line
- Word-by-word fade + rise
- Blur-to-sharp per line
- Line slides in from the right with mask
- Ink-bleed: opacity + slight scale 1.04→1 + letter-spacing settle
- Whole block revealed by a horizontal light sweep
- Typewriter-feel: pen mask in short steps (steps(6)) with a thin glowing caret moving right→left

## Spacing rules (hard)
- Calligraphic fonts are tall: line-height ≥ 1.9 and stacked lines get gap ≥ 0.6em (flex column gap).
- After building, zoom-snapshot every multi-line block (`snapshot --zoom "#id" --zoom-scale 1`) and check that
  no dot, descender or ascender touches or overlaps another line. Fix before rendering.
- Max ~20 characters per visual line; split, never shrink below 70px.

## Footage treatment
- Dark gradient overlay so text reads (top and middle darker); vary its color tint per piece
  (cool blue night, warm amber, desaturated grey, soft rose dusk).
- Slow the clip (data-playback-rate 0.7–0.9) to reach 22–30 s; never loop visibly.
