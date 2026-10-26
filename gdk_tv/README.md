# gdk_tv — automated Persian news page

Renderer used by the scheduled tasks that publish to the Instagram page **gdk_tv**.
Separate from terapi_khone: nothing here is used by the terapi_khone tasks.

- `render.py` — `render()` makes the 1080x1350 branded post, `story_from()` the 1080x1920 story,
  `render_reel()` a silent 1080x1920 reel that opens on the branded card, `commons_photo()` downloads
  a free-licence photo from Wikimedia Commons.
