"""gdk_tv news post renderer (1080x1350 post + 1080x1920 story)."""
import os, io, tarfile, requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/mnt/files/gdk"
FONTS = BASE + "/fonts/"
FD = FONTS + "Vazirmatn-FD-"
ARC = FONTS + "archivo-latin-900-normal.woff"
RED = (230, 57, 70); WHITE = (255, 255, 255); BLACK = (10, 12, 16); GREY = (205, 210, 218)
W, H = 1080, 1350; S = 2
UA = {"User-Agent": "gdk-news/1.0 (instagram gdk_tv)"}


def ensure_fonts():
    os.makedirs(FONTS, exist_ok=True)
    if os.path.exists(FD + "Black.ttf") and os.path.exists(ARC):
        return
    for url in ["https://registry.npmjs.org/vazirmatn/-/vazirmatn-33.0.3.tgz",
                "https://registry.npmjs.org/@fontsource/archivo/-/archivo-5.3.0.tgz"]:
        tf = tarfile.open(fileobj=io.BytesIO(requests.get(url, timeout=60).content))
        for m in tf.getmembers():
            n = m.name
            if ("Farsi-Digits/fonts/ttf/Vazirmatn-FD-" in n and n.endswith(".ttf")) or n.endswith("archivo-latin-900-normal.woff"):
                open(FONTS + os.path.basename(n), "wb").write(tf.extractfile(m).read())


def F(w, s):
    return ImageFont.truetype(FD + w + ".ttf", int(s * S), layout_engine=ImageFont.Layout.RAQM)


def tlen(f, t):
    return f.getlength(t, direction="rtl", language="fa")


def text(d, xy, t, f, fill, anchor="rs", stroke=2):
    x, y = xy
    d.text((x + 2 * S, y + 3 * S), t, font=f, fill=(0, 0, 0, 150), anchor=anchor, direction="rtl", language="fa")
    d.text((x, y), t, font=f, fill=fill, anchor=anchor, direction="rtl", language="fa",
           stroke_width=int(stroke * S), stroke_fill=(0, 0, 0))


def wrap(runs, maxw, base, emph):
    """runs: [(text, kind)] kind n=normal, e=big white, r=big red (underlined)."""
    words = [(w, k) for t, k in runs for w in t.split()]
    lines = [[]]; cur = 0
    for w, k in words:
        f = base if k == "n" else emph
        ww = tlen(f, w); sp = base.size * 0.28
        if lines[-1] and cur + sp + ww > maxw:
            lines.append([]); cur = 0
        cur += (sp if lines[-1] else 0) + ww
        lines[-1].append((w, k, f, ww))
    return lines


def draw_lines(d, lines, right, y, base, lh, underline=False):
    for ln in lines:
        x = right
        y += max(f.size for _, _, f, _ in ln) * 0.95
        for w, k, f, ww in ln:
            text(d, (x, y), w, f, RED if k == "r" else WHITE)
            if k == "r" and underline:
                bb = d.textbbox((x, y), w, font=f, anchor="rs", direction="rtl", language="fa")
                uy = y + f.size * 0.30
                d.rectangle([bb[0], uy, bb[2], uy + 6 * S], fill=RED)
            x -= ww + base.size * 0.28
        y += lh * S
    return y


def pill(d, right, top, label, f, padx, h, dot=False):
    bb = d.textbbox((0, 0), label, font=f, anchor="ls", direction="rtl", language="fa")
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    r = f.size * 0.16; gap = f.size * 0.28
    extra = (2 * r + gap) if dot else 0
    left = right - (tw + 2 * padx + extra)
    d.rounded_rectangle([left, top, right, top + h], radius=h * 0.18, fill=RED)
    cx = left + padx + tw / 2; cy = top + h / 2
    d.text((cx - (bb[0] + tw / 2), cy - (bb[1] + th / 2)), label, font=f, fill=WHITE, anchor="ls", direction="rtl", language="fa")
    if dot:
        dx = right - padx - r
        d.ellipse([dx - r, cy - r, dx + r, cy + r], fill=WHITE)
    return h


def logo(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK)
    d.ellipse([cx - r + 4 * S, cy - r + 4 * S, cx + r - 4 * S, cy + r - 4 * S], outline=RED, width=4 * S)
    af = ImageFont.truetype(ARC, int(r * 0.62)); tf = ImageFont.truetype(ARC, int(r * 0.29))
    d.text((cx, cy + r * 0.07), "GDK", font=af, fill=WHITE, anchor="ms")
    tw = tf.getlength("TV")
    d.rounded_rectangle([cx - tw / 2 - r * 0.15, cy + r * 0.2, cx + tw / 2 + r * 0.15, cy + r * 0.62], radius=r * 0.08, fill=RED)
    d.text((cx, cy + r * 0.53), "TV", font=tf, fill=WHITE, anchor="ms")


def brand_strip(d, R, source):
    sh = 78 * S; y0 = H * S - sh
    d.rectangle([0, y0, W * S, H * S], fill=BLACK)
    d.rectangle([0, y0, W * S, y0 + 5 * S], fill=RED)
    d.rectangle([0, y0, 250 * S, H * S], fill=RED)
    af = ImageFont.truetype(ARC, int(40 * S))
    d.text((40 * S, y0 + 56 * S), "GDK", font=af, fill=WHITE, anchor="ls")
    d.text((40 * S + af.getlength("GDK") + 12 * S, y0 + 56 * S), "TV", font=af, fill=BLACK, anchor="ls")
    # instagram icon, then GDK_TV, then source: all on one centre line
    hf = ImageFont.truetype(ARC, int(24 * S))
    cy = y0 + 41 * S; s = 30 * S; ix = 272 * S; iy = cy - s / 2; lw = int(3 * S)
    d.rounded_rectangle([ix, iy, ix + s, iy + s], radius=s * 0.28, outline=GREY, width=lw)
    cr = s * 0.22; d.ellipse([ix + s / 2 - cr, iy + s / 2 - cr, ix + s / 2 + cr, iy + s / 2 + cr], outline=GREY, width=lw)
    dr = s * 0.06; d.ellipse([ix + s * 0.76 - dr, iy + s * 0.24 - dr, ix + s * 0.76 + dr, iy + s * 0.24 + dr], fill=GREY)
    hx = ix + s + 10 * S
    hb = d.textbbox((0, 0), "GDK_TV", font=hf, anchor="ls"); cb = d.textbbox((0, 0), "GDKTV", font=hf, anchor="ls")
    base_y = cy - (cb[1] + cb[3]) / 2
    d.text((hx - hb[0], base_y), "GDK_TV", font=hf, fill=GREY, anchor="ls")
    d.text((R, base_y), "منبع: " + source, font=F("Regular", 26), fill=GREY, anchor="rs", direction="rtl", language="fa")


def render(photo, out, kicker, runs, source, breaking=False, style="A", focus_y=0.3, sub=None):
    """style A: kicker + red line; B: red vertical bar; C: kicker in red box + underlined red words."""
    ensure_fonts()
    im = Image.open(photo).convert("RGB")
    sw, sh = im.size; tr = W / H
    if sw / sh > tr:
        nw = int(sh * tr); x0 = (sw - nw) // 2; im = im.crop((x0, 0, x0 + nw, sh))
    else:
        nh = int(sw / tr); y0 = int(max(0, min(sh - nh, focus_y * sh - nh * 0.35))); im = im.crop((0, y0, sw, y0 + nh))
    im = im.resize((W * S, H * S), Image.LANCZOS).convert("RGBA")
    g = Image.new("L", (1, H * S))
    for y in range(H * S):
        t = y / (H * S); v = 0
        if t > 0.40: v = int(min(1, (t - 0.40) / 0.38) ** 1.4 * 235)
        if t < 0.16: v = max(v, int((1 - t / 0.16) * 120))
        g.putpixel((0, y), v)
    im = Image.composite(Image.new("RGBA", im.size, (0, 0, 0, 255)), im, g.resize((W * S, H * S)))
    d = ImageDraw.Draw(im)
    M = 60 * S; R = W * S - M
    logo(d, M + 56 * S, M + 60 * S, 56 * S)
    if breaking:
        pill(d, R, M + 24 * S, "فوری", F("Black", 36), 26 * S, 72 * S, dot=True)
    base = F("Bold", 64); emph = F("Black", 80); kf = F("Medium", 40); subf = F("Medium", 38)
    maxw = (W - 120 - (30 if style == "B" else 0)) * S
    lines = wrap(runs, maxw, base, emph)
    lh = 24 if style == "C" else 14
    hh = sum(max(f.size for _, _, f, _ in ln) * 0.95 + lh * S for ln in lines)
    kh = kf.size * 1.6 if kicker else 0
    subl = wrap([(sub, "n")], maxw, subf, subf) if sub else []
    shh = sum(38 * S + 14 * S for _ in subl) + (30 * S if sub else 0)
    top = H * S - 130 * S - hh - kh - 34 * S - shh
    right = R - (30 * S if style == "B" else 0)
    y = top
    if style == "B":
        d.rectangle([R - 8 * S, top - 10 * S, R, top + kh + hh + 20 * S], fill=RED)
    if kicker and style == "C":
        y += pill(d, right, y, kicker, kf, 24 * S, int(kf.size * 1.6))
    elif kicker:
        y += kf.size * 1.1; text(d, (right, y), kicker, kf, GREY if style == "B" else WHITE); y += kf.size * 0.5
    if style == "A":
        y += 10 * S; d.rectangle([right - 300 * S, y, right, y + 7 * S], fill=RED); y += 24 * S
    else:
        y += 18 * S
    y = draw_lines(d, lines, right, y, base, lh, underline=(style == "C"))
    if sub:
        y += 8 * S
        if style != "C":
            d.rectangle([right - 160 * S, y, right, y + 5 * S], fill=RED)
        y += 10 * S
        draw_lines(d, subl, right, y, subf, 14)
    brand_strip(d, R, source)
    im.convert("RGB").resize((W, H), Image.LANCZOS).save(out, quality=93)
    return out


def story_from(post_path, out):
    p = Image.open(post_path).convert("RGB")
    bg = p.resize((1536, 1920)).crop((228, 0, 1308, 1920)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.55)
    bg.paste(p, (0, (1920 - 1350) // 2)); bg.save(out, quality=93)
    return out


def render_reel(photo, post_path, details, source, out, work="/tmp/gdkreel"):
    """Reel 1080x1920 ~12-15s, silent.
    Opens with the branded post card (logo, «فوری», headline, source) for 4s,
    then one full-screen 9:16 frame per detail (2-3 s each). details: [dict(kicker, runs, sub, style)]."""
    import subprocess
    global H
    os.makedirs(work, exist_ok=True)
    frames = [story_from(post_path, work + "/f0.jpg")]
    old = H; H = 1920
    try:
        for i, dt in enumerate(details, 1):
            frames.append(render(photo, work + "/f%d.jpg" % i, dt.get("kicker"), dt["runs"], source,
                                 breaking=False, style=dt.get("style", "A"), sub=dt.get("sub")))
    finally:
        H = old
    durs = [4.0] + [3.5] * (len(frames) - 1); fd = 0.5; fps = 30
    inputs = []; parts = []
    for i, (f, d_) in enumerate(zip(frames, durs)):
        inputs += ["-loop", "1", "-t", str(d_ + fd), "-i", f]
        n = int((d_ + fd) * fps)
        parts.append("[%d:v]scale=2160:3840,zoompan=z='min(1+0.0009*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=1080x1920:fps=%d,setsar=1,format=yuv420p[v%d]" % (i, n, fps, i))
    chain = "v0"; t = durs[0]
    for i in range(1, len(frames)):
        parts.append("[%s][v%d]xfade=transition=fade:duration=%s:offset=%s[x%d]" % (chain, i, fd, t, i))
        chain = "x%d" % i; t += durs[i]
    total = sum(durs) + fd
    cmd = ["ffmpeg", "-y"] + inputs + ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", ";".join(parts), "-map", "[%s]" % chain, "-map", "%d:a" % len(frames),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(fps),
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def commons_photo(title, out):
    """Download a Wikimedia Commons file (title 'File:...') at 1920px; returns (path, license, artist)."""
    import re
    r = requests.get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": 1920, "format": "json"}, headers=UA, timeout=30).json()
    ii = list(r["query"]["pages"].values())[0]["imageinfo"][0]; m = ii["extmetadata"]
    open(out, "wb").write(requests.get(ii.get("thumburl") or ii["url"], headers=UA, timeout=60).content)
    lic = m.get("LicenseShortName", {}).get("value", "")
    artist = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", ""))
    return out, lic, artist
