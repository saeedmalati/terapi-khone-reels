# terapi-khone-reels

Content for the Instagram page terapi_khone (fully automatic, every 3 hours).

- `template/reel-video/` — HyperFrames reel template over real footage (1080×1920): calligraphic fonts
  (Nastaliq, Gulzar, Ruqaa), RTL pen-mask reveal, watermark. Put the clip at `assets/footage.mp4` and the
  cut song segment at `assets/music.wav`.
- `template/` (root files) — older illustrated template (SVG landscape), kept as a fallback when no footage.
- `music/` — the ONLY source of music: the user's own uploaded songs (`ba-kalam/` with vocals, `bi-kalam/` instrumental),
  catalogued in `music/list.md` with mood and best segment. `template/music.py` is retired; never compose music.
- `tools/fetch_footage.py` — run inside the Composio remote workbench (it can reach Pixabay); commits the clip
  to `footage/<id>-<slug>.mp4.partNN`. Reassemble with `cat footage/<name>.mp4.part* > assets/footage.mp4`.
  Unused footage already in `footage/`: none.
- `STYLES.md` — fonts, layouts, reveals and HARD spacing rules. Never repeat the style of the last 3 pieces.
- `reels/`, `posts/` — published files (their raw.githubusercontent.com URLs are what Instagram fetches).
- `log.json` — everything published, with type, topic, title, permalink, story, music params and style.
