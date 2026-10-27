"""gdk_tv news renderer: 1080x1350 post, 1080x1920 story and 1080x1920 reel.
Reel: no zoom (very slow pan), soft typed text with real keystroke sounds, 4.5 s hold, spinning 3D GDK_TV
globe transition (none at the start), soft low whoosh, original news music bed that changes every run.
Run render_reel in a background process (it takes ~4-5 min) and keep files on disk (/home/user), not /tmp."""
import os, io, tarfile, requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.environ.get("GDK_BASE", "/home/user/gdk" if os.path.isdir("/home/user") else "/tmp/gdk")
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



def _reel_ops(kicker, runs, sub, style, RH, bottom=330):
    M = 60 * S; R = W * S - M
    base = F("Bold", 68); emph = F("Black", 86); kf = F("Medium", 42); subf = F("Medium", 40)
    maxw = (W - 120 - (30 if style == "B" else 0)) * S
    lines = wrap(runs, maxw, base, emph)
    lh = 26 if style == "C" else 16
    hh = sum(max(f.size for _, _, f, _ in ln) * 0.95 + lh * S for ln in lines)
    kh = kf.size * 1.6 if kicker else 0
    subl = wrap([(sub, "n")], maxw, subf, subf) if sub else []
    shh = sum(40 * S + 16 * S for _ in subl) + (30 * S if sub else 0)
    top = RH * S - bottom * S - hh - kh - 34 * S - shh
    right = R - (30 * S if style == "B" else 0)
    ops = []; y = top
    if style == "B":
        box = [R - 8 * S, top - 10 * S, R, top + kh + hh + 20 * S]
        ops.append(("s", lambda d, b=box: d.rectangle(b, fill=RED)))
    if kicker and style == "C":
        hp = int(kf.size * 1.6); yy = y
        ops.append(("s", lambda d, yy=yy, hp=hp: pill(d, right, yy, kicker, kf, 24 * S, hp)))
        y += hp
    elif kicker:
        y += kf.size * 1.1
        ops.append(("w", right, y, kicker, kf, GREY if style == "B" else WHITE, False))
        y += kf.size * 0.5
    if style == "A":
        y += 10 * S; box = [right - 300 * S, y, right, y + 7 * S]
        ops.append(("s", lambda d, b=box: d.rectangle(b, fill=RED))); y += 24 * S
    else:
        y += 18 * S
    def add_lines(lns, y, sp_font, lhh, ul):
        for ln in lns:
            x = right
            y += max(f.size for _, _, f, _ in ln) * 0.95
            for w, k, f, ww in ln:
                ops.append(("w", x, y, w, f, RED if k == "r" else WHITE, ul and k == "r"))
                x -= ww + sp_font.size * 0.28
            y += lhh * S
        return y
    y = add_lines(lines, y, base, lh, style == "C")
    if sub:
        y += 8 * S
        if style != "C":
            box = [right - 160 * S, y, right, y + 5 * S]
            ops.append(("s", lambda d, b=box: d.rectangle(b, fill=RED)))
        y += 10 * S
        add_lines(subl, y, subf, 16, False)
    return ops


def _draw_ops(d, ops, n):
    for op in ops:
        if op[0] == "s":
            if n < 0:
                break
            op[1](d); continue
        _, x, y, w, f, fill, ul = op
        if n <= 0:
            n = -1; break
        k = min(len(w), n)
        text(d, (x, y), w[:k], f, fill)
        if k == len(w) and ul:
            bb = d.textbbox((x, y), w, font=f, anchor="rs", direction="rtl", language="fa")
            uy = y + f.size * 0.30
            d.rectangle([bb[0], uy, bb[2], uy + 6 * S], fill=RED)
        n -= k
        if k < len(w):
            n = -1; break


def _rgba_down(im, size):
    return im.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")


def _cover_size(photo, w, h, focus_y=0.3):
    im = Image.open(photo).convert("RGB")
    sw, sh = im.size; tr = w / h
    if sw / sh > tr:
        nw = int(sh * tr); x0 = (sw - nw) // 2; im = im.crop((x0, 0, x0 + nw, sh))
    else:
        nh = int(sw / tr); y0 = int(max(0, min(sh - nh, focus_y * sh - nh * 0.35))); im = im.crop((0, y0, sw, y0 + nh))
    return im.resize((w, h), Image.LANCZOS)


class _Scene:
    def __init__(self, sc, source, breaking, RH, duration, pan_px=110):
        self.RH = RH; self.dur = duration
        self.pan = sc.get("pan", "lr")
        self.px = pan_px
        horiz = self.pan in ("lr", "rl")
        pw, ph = (W + pan_px, RH) if horiz else (W, RH + pan_px)
        self.photo = _cover_size(sc["photo"], pw, ph, sc.get("focus_y", 0.3))
        ov = Image.new("RGBA", (W * S, RH * S), (0, 0, 0, 0))
        g = Image.new("L", (1, RH * S))
        for y in range(RH * S):
            t = y / (RH * S); v = 0
            if t > 0.36: v = int(min(1, (t - 0.36) / 0.36) ** 1.3 * 240)
            if t < 0.14: v = max(v, int((1 - t / 0.14) * 130))
            g.putpixel((0, y), v)
        ov.putalpha(g.resize((W * S, RH * S)))
        d = ImageDraw.Draw(ov)
        M = 60 * S; R = W * S - M; top = 150 * S
        logo(d, M + 62 * S, top + 62 * S, 62 * S)
        if breaking:
            pill(d, R, top + 26 * S, "فوری", F("Black", 38), 26 * S, 76 * S, dot=True)
        global H
        old = H; H = RH
        try:
            brand_strip(d, R, source)
        finally:
            H = old
        self.overlay = _rgba_down(ov, (W, RH))
        self.ops = _reel_ops(sc.get("kicker"), sc["runs"], sc.get("sub"), sc.get("style", "A"), RH)
        self.total = sum(len(o[3]) for o in self.ops if o[0] == "w")
        self._layers = {}

    def layer(self, n):
        if n not in self._layers:
            if len(self._layers) > 3:
                for key in sorted(self._layers)[:-2]:
                    del self._layers[key]
            im = Image.new("RGBA", (W * S, self.RH * S), (0, 0, 0, 0))
            _draw_ops(ImageDraw.Draw(im), self.ops, n)
            self._layers[n] = _rgba_down(im, (W, self.RH))
        return self._layers[n]

    def photo_at(self, t):
        u = max(0.0, min(1.0, t / self.dur))
        u = u * u * (3 - 2 * u) * 0.85 + u * 0.15
        off = u * self.px
        if self.pan in ("rl", "bt"):
            off = self.px - off
        if self.pan in ("lr", "rl"):
            a = (1, 0, off, 0, 1, 0)
        else:
            a = (1, 0, 0, 0, 1, off)
        return self.photo.transform((W, self.RH), Image.AFFINE, a, resample=Image.BICUBIC).convert("RGBA")

    def frame(self, t, chars):
        im = self.photo_at(t)
        im.alpha_composite(self.overlay)
        if chars > 0:
            k = int(chars); fr = chars - k
            lay = self.layer(min(k, self.total))
            if fr > 0.02 and k < self.total:
                lay = Image.blend(lay, self.layer(k + 1), fr)
            im.alpha_composite(lay)
        return im.convert("RGB")


_GLOBE_TEX = None


def _globe_texture():
    global _GLOBE_TEX
    if _GLOBE_TEX is not None:
        return _GLOBE_TEX
    import numpy as np
    TW, TH = 4096, 2048
    tex = Image.new("RGB", (TW, TH), BLACK)
    d = ImageDraw.Draw(tex)
    for i in range(TH):
        c = int(14 + 10 * (1 - abs(i / TH - 0.5) * 2))
        d.line([(0, i), (TW, i)], fill=(c, c + 2, c + 8))
    rnd = __import__("random").Random(7)
    for _ in range(2600):
        x = rnd.randrange(TW); y = int(TH * (0.15 + 0.7 * rnd.random()))
        r = rnd.choice([2, 3, 3, 4])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(70, 74, 84))
    for k in range(0, 360, 20):
        x = int(k / 360 * TW); d.rectangle([x - 3, 0, x + 3, TH], fill=(150, 40, 50))
    for k in range(-80, 81, 20):
        y = int((0.5 - k / 180) * TH); d.rectangle([0, y - 3, TW, y + 3], fill=(150, 40, 50))
    d.rectangle([0, TH // 2 - 6, TW, TH // 2 + 6], fill=RED)
    L = 820
    lg = Image.new("RGBA", (L * 2, L * 2), (0, 0, 0, 0))
    logo(ImageDraw.Draw(lg), L, L, L - 8)
    lg = _rgba_down(lg, (L, L))
    tex.paste(lg, (TW // 2 - L // 2, TH // 2 - L // 2), lg)
    af = ImageFont.truetype(ARC, 210)
    for cx in (0, TW):
        d.text((cx, TH // 2 + 75), "GDK_TV", font=af, fill=WHITE, anchor="ms")
    _GLOBE_TEX = np.asarray(tex).copy()
    return _GLOBE_TEX


def _globe_over(base, cx, cy, r, theta, tilt=0.14):
    import numpy as np, math
    tex = _globe_texture(); TH, TW = tex.shape[:2]
    Wb, Hb = base.size
    x0, x1 = max(0, int(cx - r - 2)), min(Wb, int(cx + r + 3))
    y0, y1 = max(0, int(cy - r - 2)), min(Hb, int(cy + r + 3))
    if x1 <= x0 or y1 <= y0 or r < 2:
        return base
    Lx, Ly, Lz = -0.45, 0.55, 0.70
    ln = math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz); Lx, Ly, Lz = Lx / ln, Ly / ln, Lz / ln
    ct, st = math.cos(tilt), math.sin(tilt)
    c, s = math.cos(-theta), math.sin(-theta)
    rimc = np.array([0.90, 0.22, 0.27], dtype=np.float32) * 0.75
    for ya in range(y0, y1, 160):
        yb = min(y1, ya + 160)
        ys, xs = np.mgrid[ya:yb, x0:x1].astype(np.float32)
        nx = (xs + 0.5 - cx) / r; ny = -(ys + 0.5 - cy) / r
        del xs, ys
        rr = nx * nx + ny * ny
        alpha = np.clip((1.0 - np.sqrt(rr)) * r + 0.5, 0, 1)
        if not alpha.any():
            continue
        nz = np.sqrt(np.clip(1 - rr, 0, 1))
        py = ny * ct - nz * st; pz = ny * st + nz * ct
        qx = nx * c + pz * s; qz = -nx * s + pz * c
        u = ((np.arctan2(qx, qz) / (2 * math.pi) + 0.5) * (TW - 1)).astype(np.int32) % TW
        v = ((0.5 - np.arcsin(np.clip(py, -1, 1)) / math.pi) * (TH - 1)).astype(np.int32).clip(0, TH - 1)
        col = tex[v, u].astype(np.float32) / 255.0
        dif = np.clip(nx * Lx + ny * Ly + nz * Lz, 0, 1)
        spec = np.clip(2 * dif * nz - Lz, 0, 1) ** 28 * 0.45
        rim = (1 - nz) ** 3
        out = col * (0.32 + 0.85 * dif)[..., None] + spec[..., None] + rim[..., None] * rimc
        out = np.clip(out, 0, 1)
        bb = np.asarray(base.crop((x0, ya, x1, yb))).astype(np.float32) / 255.0
        a = alpha[..., None]
        mix = (out * a + bb * (1 - a)) * 255.0
        base.paste(Image.fromarray(mix.astype(np.uint8)), (x0, ya))
    return base


def _globe_path(t, RH):
    import math
    def ease(u):
        u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
    full = math.hypot(W / 2, RH / 2) + 60
    if t <= 0.5:
        u = ease(t / 0.5)
        cx = -260 + (W / 2 + 260) * u; cy = RH + 260 - (RH / 2 + 260) * u
        r = 110 + (full - 110) * u ** 1.6
    else:
        u = ease((t - 0.5) / 0.5)
        cx = W / 2 + (W / 2 + 300) * u; cy = RH / 2 - (RH / 2 + 300) * u
        r = full - (full - 120) * u ** 0.7
    theta = (t - 0.5) * math.pi * 1.7
    return cx, cy, r, theta


_SR = 48000


def _ffmpeg():
    import shutil, subprocess
    ff = shutil.which("ffmpeg")
    if not ff:
        try:
            import imageio_ffmpeg
        except ImportError:
            subprocess.run(["pip", "install", "-q", "imageio-ffmpeg"], check=True)
            import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    return ff


_KEYS = None
KEY_SOUNDS = ("File:Laptop keyboard.ogg", "File:Typing medium speed.ogg")


def _key_bank():
    global _KEYS
    if _KEYS is not None:
        return _KEYS
    import numpy as np, subprocess
    hits = []
    try:
        ff = _ffmpeg()
        for title in KEY_SOUNDS:
            r = requests.get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url", "format": "json"},
                headers=UA, timeout=30).json()
            url = list(r["query"]["pages"].values())[0]["imageinfo"][0]["url"]
            raw = requests.get(url, headers=UA, timeout=60).content
            pcm = subprocess.run([ff, "-v", "error", "-i", "-", "-ac", "1", "-ar", str(_SR), "-f", "f32le", "-"],
                                 input=raw, capture_output=True, check=True).stdout
            x = np.frombuffer(pcm, dtype=np.float32).astype(np.float64)
            x = x - np.convolve(x, np.ones(600) / 600, mode="same")
            e = np.convolve(np.abs(x), np.ones(96) / 96, mode="same")
            thr = max(np.percentile(e, 99.5) * 0.30, np.median(e) * 8)
            above = e > thr
            starts = np.flatnonzero(above[1:] & ~above[:-1]) + 1
            last = -10 ** 9; gap = int(0.09 * _SR); L = int(0.12 * _SR)
            for s in starts:
                if s - last < gap:
                    continue
                last = s
                a = max(0, s - int(0.004 * _SR)); seg = x[a:a + L].copy()
                if len(seg) < L or np.abs(seg).max() < 1e-4:
                    continue
                fl = int(len(seg) * 0.45)
                seg[-fl:] *= np.linspace(1, 0, fl) ** 2
                seg[:24] *= np.linspace(0, 1, 24)
                hits.append(seg / np.abs(seg).max())
        hits.sort(key=lambda h: float(np.sqrt((h[: int(0.03 * _SR)] ** 2).mean())))
        hits = hits[len(hits) // 10: len(hits) - len(hits) // 10][:120]
    except Exception as ex:
        print("key sounds unavailable:", ex)
        hits = []
    _KEYS = hits
    return _KEYS


def _onepole_lp(x, fc):
    import numpy as np, math
    a = math.exp(-2 * math.pi * fc / _SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y


def _sfx_click(rng):
    import numpy as np
    n = int(0.04 * _SR); t = np.arange(n) / _SR
    x = rng.standard_normal(n) * np.exp(-t / 0.005) * 0.6 + np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.008) * 0.5
    x = _onepole_lp(x, 4000)
    return x / (np.abs(x).max() + 1e-9)


def _sfx_whoosh(dur, rng):
    import numpy as np, math
    n = int(dur * _SR); t = np.arange(n) / dur / _SR
    x = rng.standard_normal(n)
    fc = 220 + 1100 * np.sin(np.pi * t) ** 1.6
    y = np.empty(n); acc = 0.0; acc2 = 0.0
    for i in range(n):
        a = math.exp(-2 * math.pi * fc[i] / _SR)
        acc = (1 - a) * x[i] + a * acc
        acc2 = (1 - a) * acc + a * acc2
        y[i] = acc2
    y = y - _onepole_lp(y, 110)
    env = np.sin(np.pi * np.clip(t, 0, 1)) ** 1.6
    y = y * env
    return y / (np.abs(y).max() + 1e-9)


def _news_music(total_s, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    sr = _SR; n = int(total_s * sr) + sr
    L = np.zeros(n); R = np.zeros(n)
    bpm = float(rng.integers(100, 129))
    root = 62 + int(rng.integers(-5, 5))
    scale = [0, 2, 3, 5, 7, 8, 10]
    progs = [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 6], [0, 4, 5, 3], [5, 6, 0, 0], [0, 2, 6, 3],
             [0, 5, 3, 4], [3, 0, 5, 6], [0, 0, 5, 6], [5, 3, 0, 4], [0, 6, 3, 4], [0, 3, 6, 2]]
    prog = progs[int(rng.integers(len(progs)))]
    pats = [[0, 1, 2, 1, 3, 2, 1, 2], [0, 2, 1, 2, 0, 2, 3, 2], [0, 1, 2, 3, 2, 1, 0, 1],
            [3, 2, 1, 0, 1, 2, 1, 2], [0, 0, 2, 1, 0, 0, 3, 2], [0, 2, 3, 2, 1, 2, 0, 2],
            [0, 1, 0, 2, 0, 3, 0, 2], [2, 1, 0, 1, 2, 3, 2, 1]]
    pat = pats[int(rng.integers(len(pats)))]
    sixteenth = rng.random() < 0.35 and bpm < 112
    hdec = rng.uniform(0.74, 0.9); nh = int(rng.integers(6, 11))
    sdec = rng.uniform(0.07, 0.15)
    bell = rng.random() < 0.5; pluck = rng.random() < 0.4; answer = rng.random() < 0.7
    hat_on = rng.random() < 0.8
    hz = lambda m: 440.0 * 2 ** ((m - 69) / 12.0)

    def chord(deg):
        notes = []
        for k in (0, 2, 4):
            d = deg + k; o = 12 * (d // 7)
            notes.append(root + scale[d % 7] + o)
        if deg == 4 and rng.random() < 0.5:
            notes[1] += 1
        return notes
    chords = [chord(d) for d in prog]

    def add(sig, t0, l, r):
        i = int(t0 * sr)
        if i < 0:
            sig = sig[-i:]; i = 0
        j = min(n, i + len(sig))
        if i >= n or j <= i: return
        L[i:j] += sig[:j - i] * l; R[i:j] += sig[:j - i] * r

    beat = 60.0 / bpm; step = beat / (4 if sixteenth else 2); bar = beat * 4
    steps = 16 if sixteenth else 8
    tn = np.arange(int(0.32 * sr)) / sr
    env_s = (1 - np.exp(-tn / 0.006)) * np.exp(-tn / sdec)
    def string(f, det, ph=0.7):
        w = np.zeros_like(tn)
        for h in range(1, nh + 1):
            w += np.sin(2 * np.pi * f * det * h * tn + h * ph) / h * hdec ** h
        return w * env_s
    tb = np.arange(int(1.2 * sr)) / sr
    def bell_tone(f):
        return (np.sin(2 * np.pi * f * tb) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tb)) * np.exp(-tb / 0.35)
    tq = np.arange(int(0.25 * sr)) / sr
    def pluck_tone(f):
        return (np.sin(2 * np.pi * f * tq) + 0.3 * np.sin(4 * np.pi * f * tq)) * np.exp(-tq / 0.06)
    tp = np.arange(int((bar + 0.6) * sr)) / sr
    env_p = np.minimum(1, tp / 0.45) * np.minimum(1, (tp[-1] - tp) / 0.45)
    th = np.arange(int(0.05 * sr)) / sr
    env_h = np.exp(-th / 0.010)

    nbars = int(total_s / bar) + 2
    for b in range(nbars):
        t_bar = b * bar
        ch = chords[b % len(chords)]
        pad = np.zeros_like(tp)
        for m in ch:
            f = hz(m - 12)
            pad += np.sin(2 * np.pi * f * tp) + 0.25 * np.sin(4 * np.pi * f * tp)
        add(pad * env_p * 0.10, t_bar - 0.3, 1.0, 1.0)
        for k in range(steps):
            idx = pat[k % 8]
            t = t_bar + k * step
            m = ch[0] + 12 if idx == 3 else ch[idx]
            acc = 1.0 if k % 2 == 0 else 0.72
            g = 0.30 * (0.8 if sixteenth else 1.0) * acc
            add(string(hz(m), 1.0) * g, t, 1.0, 0.75)
            add(string(hz(m), 1.004) * g, t + 0.004, 0.75, 1.0)
            if hat_on and (not sixteenth or k % 2 == 0):
                noise = np.diff(rng.standard_normal(len(th) + 1)) * env_h
                add(noise * (0.035 if k % 2 else 0.022), t, 0.8, 1.0)
        if pluck:
            for k in (0, 3, 6):
                add(pluck_tone(hz(ch[0] - 12)) * 0.12, t_bar + k * beat / 2, 1.0, 1.0)
        if bell and b % 2 == 0:
            add(bell_tone(hz(ch[2] + 12)) * 0.07, t_bar, 0.9, 1.0)
        if answer and b % 2 == 1:
            for k, m in enumerate((ch[2] + 12, ch[1] + 12)):
                add(string(hz(m), 1.002) * 0.16, t_bar + bar * 0.75 + k * beat / 2, 0.9, 0.9)
    st = np.stack([L, R], 1)[: int(total_s * sr)]
    tt = np.arange(len(st)) / sr
    fade = np.minimum(1, tt / 1.2) * np.minimum(1, (total_s - tt) / 1.8)
    st *= np.clip(fade, 0, 1)[:, None]
    return st / (np.abs(st).max() + 1e-9)


def _soundtrack(total_s, clicks, whooshes, sting, music=0.13, music_seed=0):
    import numpy as np
    rng = np.random.default_rng(music_seed + 11)
    L = np.zeros(int(total_s * _SR) + _SR); R = np.zeros_like(L)
    CLICK, WHOOSH = 0.08, 0.10
    bank = _key_bank()
    for tc in clicks:
        if bank:
            c = bank[int(rng.integers(len(bank)))] * rng.uniform(0.6, 0.95)
        else:
            c = _sfx_click(rng) * rng.uniform(0.55, 0.85)
        c = c * CLICK
        i = int((tc + rng.uniform(-0.012, 0.012)) * _SR)
        if i < 0 or i >= len(L):
            continue
        pan = rng.uniform(-0.15, 0.15); c = c[: len(L) - i]
        L[i:i + len(c)] += c * (1 - pan); R[i:i + len(c)] += c * (1 + pan)
    for ts, p0, p1 in whooshes:
        w = _sfx_whoosh(sting * 1.15, rng) * WHOOSH
        i = int(ts * _SR)
        if i < 0:
            w = w[-i:]; i = 0
        w = w[: len(L) - i]
        p = np.linspace(p0, p1, len(w))
        L[i:i + len(w)] += w * (1 - p) / 1.4; R[i:i + len(w)] += w * (1 + p) / 1.4
    st = np.stack([L, R], 1)[: int(total_s * _SR)]
    if music:
        st += _news_music(total_s, music_seed) * music
    st = np.clip(st, -0.9, 0.9)
    return (st * 32767).astype(np.int16)


def render_reel(scenes, source, out, breaking=False, hold=4.5, cps=15, sting=1.6, fps=30, music_seed=None):
    import subprocess, shutil, wave, numpy as np
    ensure_fonts()
    RH = 1920
    photos = [sc["photo"] for sc in scenes]
    if len(set(photos)) != len(photos):
        raise ValueError("every scene needs a different photo")
    ff = _ffmpeg()
    if music_seed is None:
        import time as _t
        music_seed = int(_t.time() // 2700)
    pans = ["lr", "tb", "rl", "bt"]
    ns = int(sting * fps); half = ns // 2
    vid = out + ".video.mp4"
    proc = subprocess.Popen([ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, RH), "-r", str(fps),
                             "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17",
                             "-threads", "1",
                             "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    clicks = []; whooshes = []; fno = 0
    def emit(img):
        nonlocal fno
        proc.stdin.write(img.tobytes()); fno += 1
    import gc
    for i, sc in enumerate(scenes):
        sc = dict(sc); sc.setdefault("pan", pans[i % 4])
        o = _Scene(sc, source, breaking and i == 0, RH, 1.0)
        o.type_s = o.total / cps
        o.dur = half / fps + 0.25 + o.type_s + hold + half / fps
        t_scene0 = fno / fps
        if i == 0:
            k_from = ns
        else:
            whooshes.append(((fno - half) / fps, -0.6, 0.7)); k_from = half
        for k in range(k_from, ns):
            im = o.frame(fno / fps - t_scene0, 0)
            cx, cy, r, th = _globe_path(k / (ns - 1), RH)
            emit(_globe_over(im, cx, cy, r, th))
        for _ in range(int(0.25 * fps)):
            emit(o.frame(fno / fps - t_scene0, 0))
        t_type = fno / fps; nfr = max(1, int(o.type_s * fps))
        last = 0
        for f_ in range(nfr):
            chars = (f_ + 1) / nfr * o.total
            if int(chars) > last:
                for c in range(last, int(chars)):
                    clicks.append(t_type + (c / o.total) * o.type_s)
                last = int(chars)
            emit(o.frame(fno / fps - t_scene0, min(chars, o.total)))
        for _ in range(int(hold * fps)):
            emit(o.frame(fno / fps - t_scene0, o.total))
        if i + 1 < len(scenes):
            for k in range(0, half):
                im = o.frame(fno / fps - t_scene0, o.total)
                cx, cy, r, th = _globe_path(k / (ns - 1), RH)
                emit(_globe_over(im, cx, cy, r, th))
        del o; gc.collect()
        print("scene", i, "frames", fno, flush=True)
    proc.stdin.close(); proc.wait()
    total = fno / fps
    pcm = _soundtrack(total, clicks, whooshes, sting, music_seed=music_seed)
    wav = out + ".wav"
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(_SR); wf.writeframes(pcm.tobytes())
    del pcm; gc.collect()
    global _GLOBE_TEX, _KEYS
    _GLOBE_TEX = None; _KEYS = None; gc.collect()
    subprocess.run([ff, "-y", "-threads", "1", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-crf", "20", "-threads", "1",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                   check=True, capture_output=True)
    for p in (vid, wav):
        try: os.remove(p)
        except OSError: pass
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
