# terapi-khone-reels

Content for the Instagram page terapi_khone (fully automatic, every 3 hours).

- `template/reel-video/` — HyperFrames reel template over real footage (1080×1920): calligraphic fonts
  (Nastaliq, Gulzar, Ruqaa), RTL pen-mask reveal, watermark. Put the clip at `assets/footage.mp4` and the
  score at `assets/music.wav`.
- `template/` (root files) — older illustrated template (SVG landscape), kept as a fallback when no footage.
- `template/music.py` — composes an ORIGINAL emotional score every run (piano, violin, cello, strings,
  choir "aah" and voice "ooh") from real instrument samples in `template/samples/`:
  `python3 music.py out.wav --dur 26 --seed N --key D --tempo 64 --prog 0..5`
- `tools/fetch_footage.py` — run inside the Composio remote workbench (it can reach Pixabay); commits the clip
  to `footage/<id>-<slug>.mp4.partNN`. Reassemble with `cat footage/<name>.mp4.part* > assets/footage.mp4`.
  Unused footage already in `footage/`: none.
- `STYLES.md` — fonts, layouts, reveals and HARD spacing rules. Never repeat the style of the last 3 pieces.
- `reels/`, `posts/` — published files (their raw.githubusercontent.com URLs are what Instagram fetches).
- `log.json` — everything published, with type, topic, title, permalink, story, music params and style.
