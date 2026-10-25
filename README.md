# terapi-khone-reels

Content for the Instagram page terapi_khone.

- `template/` — HyperFrames template (1080×1920, Vazirmatn, write-on text, watermark).
- `template/music.py` — composes an ORIGINAL emotional score every run (piano + violin + cello + strings) from real instrument samples in `template/samples/` (MusyngKite soundfont). Usage:
  `python3 music.py out.wav --dur 26 --seed N --key A --tempo 66 --prog 0..5`
  Change seed/key/tempo/prog every time.
- `reels/` and `posts/` — published files (their raw.githubusercontent.com URLs are what Instagram fetches).
- `log.json` — everything published: type (reel/post), topic, title, permalink, story. Never repeat a topic+angle or a sentence.
