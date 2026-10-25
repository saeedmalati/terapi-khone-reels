#!/usr/bin/env python3
"""Original emotional score for terapi_khone reels: piano + violin + cello + strings + choir/voice (aah, ooh).

Uses real instrument samples vendored in samples/ (MusyngKite soundfont, free to use)
and composes a NEW piece every time from the seed, so nothing is copied and there is
no copyright claim on the music.

    python3 music.py out.wav --dur 24 --seed 7 --key A --tempo 66 --prog 0

--key   tonic of the minor key: C C# D Eb E F F# G Ab A Bb B
--prog  0..5 picks one of several emotional minor progressions
--seed  changes the melody, arpeggio pattern and voicing
"""
import argparse, os, subprocess, wave
import numpy as np
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
KEYS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
# scale degrees (natural minor, with raised 7th available for V chords)
MINOR = [0, 2, 3, 5, 7, 8, 10]
# chords as (degree-root semitone offset, quality)  m = minor triad, M = major, M7 = major with raised 7 (for V)
PROGS = [
    [(0, "m"), (8, "M"), (3, "M"), (10, "M")],   # i  VI  III VII   (classic sad pop)
    [(0, "m"), (5, "m"), (8, "M"), (7, "M")],    # i  iv  VI  V
    [(8, "M"), (10, "M"), (0, "m"), (0, "m")],   # VI VII i   i
    [(0, "m"), (10, "M"), (8, "M"), (7, "M")],   # i  VII VI  V    (lament)
    [(0, "m"), (3, "M"), (10, "M"), (5, "m")],   # i  III VII iv
    [(5, "m"), (0, "m"), (8, "M"), (7, "M")],    # iv i   VI  V
]
TRIAD = {"m": [0, 3, 7], "M": [0, 4, 7]}

_cache = {}
def sample(inst, midi):
    folder = os.path.join(HERE, "samples", inst)
    have = sorted(int(f[:-4]) for f in os.listdir(folder) if f.endswith(".mp3"))
    m = min(have, key=lambda x: abs(x - midi))
    key = (inst, m)
    if key not in _cache:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(folder, f"{m}.mp3"),
                              "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        _cache[key] = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)
    s = _cache[key]
    if m != midi:  # small pitch shift by resampling (rarely needed)
        r = 2 ** ((midi - m) / 12)
        idx = np.arange(0, len(s) - 1, r)
        s = np.stack([np.interp(idx, np.arange(len(s)), s[:, c]) for c in (0, 1)], axis=1)
    return s

def held(inst, midi, dur, attack_keep=0.7, loop=(0.8, 2.3), xf=0.35, release=0.6):
    """Sample stretched to `dur` seconds by crossfade-looping its sustain part."""
    s = sample(inst, midi)
    total = int((dur + release) * SR)
    if total <= len(s):
        out = s[:total].copy()
    else:
        a, b = int(loop[0] * SR), int(loop[1] * SR)
        seg = s[a:b]; x = int(xf * SR)
        out = s[:b].copy()
        fade = np.linspace(0, 1, x)[:, None]
        while len(out) < total:
            nxt = seg.copy()
            out[-x:] = out[-x:] * (1 - fade) + nxt[:x] * fade
            out = np.concatenate([out, nxt[x:]])
        out = out[:total]
    r = int(release * SR)
    out[-r:] *= np.linspace(1, 0, r)[:, None] ** 2
    return out

def place(buf, sig, t, gain, pan=0.0):
    i = int(t * SR)
    if i >= len(buf): return
    e = min(len(buf), i + len(sig)); sig = sig[: e - i]
    L = np.cos((pan + 1) * np.pi / 4); R = np.sin((pan + 1) * np.pi / 4)
    buf[i:e, 0] += sig[:, 0] * gain * L * 1.41
    buf[i:e, 1] += sig[:, 1] * gain * R * 1.41

def reverb_ir(seconds=3.2, seed=1):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR); t = np.arange(n) / SR
    env = np.exp(-t * 2.4)
    ir = rng.normal(0, 1, (n, 2)) * env[:, None]
    # darken the tail
    k = np.exp(-np.arange(64) / 10.0); k /= k.sum()
    ir = np.stack([np.convolve(ir[:, c], k, mode="same") for c in (0, 1)], axis=1)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())

def compose(dur, seed, key, tempo, prog_i):
    rng = np.random.default_rng(seed)
    tonic = 57 + KEYS[key]           # A3 region
    if tonic > 62: tonic -= 12
    beat = 60 / tempo; bar = 4 * beat
    prog = PROGS[prog_i % len(PROGS)]
    nbars = int(np.ceil(dur / bar)) + 1
    dry = {k: np.zeros((int((dur + 4) * SR), 2)) for k in ("piano", "violin", "cello", "strings", "choir", "voice")}
    use_voice = rng.random() < 0.85

    scale = sorted({(tonic + d + 12 * o) for d in MINOR for o in (-1, 0, 1, 2)})
    def nearest_scale(m): return min(scale, key=lambda x: abs(x - m))

    arp_patterns = [[0, 1, 2, 1, 3, 1, 2, 1], [0, 2, 1, 2, 3, 2, 1, 2], [0, 1, 2, 3, 2, 1, 2, 1]]
    pat = arp_patterns[rng.integers(len(arp_patterns))]
    prev_mel = tonic + 12 + 7

    for b in range(nbars):
        t0 = b * bar
        if t0 > dur - 1.5: break
        off, q = prog[b % len(prog)]
        root = tonic + off
        if root > tonic + 6: root -= 12
        tri = [root + x for x in TRIAD[q]]
        section = "intro" if b < 2 else ("peak" if b >= nbars - 4 and b < nbars - 2 else "body")
        last = t0 + bar > dur - bar * 0.9

        # piano: bass note + broken chord, softer in intro
        place(dry["piano"], held("acoustic_grand_piano", root - 12, bar * 0.95, release=0.8), t0, 0.55, -0.1)
        voicing = [tri[0] + 12, tri[1] + 12, tri[2] + 12, tri[0] + 24]
        for k, p in enumerate(pat):
            vel = (0.30 if section == "intro" else 0.24) * (1.0 if k % 2 == 0 else 0.8) * rng.uniform(0.9, 1.05)
            place(dry["piano"], held("acoustic_grand_piano", voicing[p], beat * 0.9, release=0.9), t0 + k * beat / 2 + rng.uniform(0, 0.012), vel, -0.25 + 0.06 * k)

        if b >= 1:
            # cello long root, strings pad
            place(dry["cello"], held("cello", root - 12 if root - 12 >= 36 else root, bar + 0.2, release=0.9), t0, 0.42 if section != "intro" else 0.28, -0.35)
            pad_gain = 0.16 if section == "intro" else (0.30 if section == "peak" else 0.22)
            for m in tri:
                place(dry["strings"], held("string_ensemble_1", m, bar + 0.3, release=1.0), t0, pad_gain, 0.3)
            if use_voice and section != "intro":
                cg = 0.20 if section == "peak" else 0.13
                for m in tri:
                    mm = m + 12 if m + 12 <= 79 else m
                    place(dry["choir"], held("choir_aahs", mm, bar + 0.3, release=1.2), t0, cg, -0.2)

        if b >= 2 and not (last and b == nbars - 1):
            # violin melody: two or three notes per bar, chord tones on strong beats, stepwise between
            octave = 12 if section != "peak" else 24
            targets = [x + octave for x in tri]
            rhythm = [[2, 2], [3, 1], [1.5, 0.5, 2], [2, 1, 1]][rng.integers(4)] if not last else [4]
            t = t0
            for i, dlen in enumerate(rhythm):
                if i == 0:
                    m = min(targets, key=lambda x: abs(x - prev_mel) + rng.uniform(0, 3))
                else:
                    m = nearest_scale(prev_mel + int(rng.choice([-2, -1, 1, 2, 3, -3], p=[.25, .2, .2, .15, .1, .1])))
                m = int(np.clip(m, 62, 88))
                d = dlen * beat
                g = (0.34 if section == "peak" else 0.27) * rng.uniform(0.92, 1.05)
                place(dry["violin"], held("violin", m, d * 1.02, release=0.7), t + 0.03, g, 0.15)
                if use_voice and section == "peak":
                    vm = m - 12 if m - 12 >= 48 else m
                    place(dry["voice"], held("voice_oohs", min(vm, 79), d * 1.02, release=0.9), t + 0.05, g * 0.8, -0.1)
                prev_mel = m; t += d

    # final chord
    end_t = max(0, dur - bar * 0.9)
    for m in (tonic - 12, tonic, tonic + 3, tonic + 7, tonic + 12):
        place(dry["piano"], held("acoustic_grand_piano", m, bar, release=1.6), end_t, 0.22, 0)
    return dry

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--dur", type=float, default=24)
    ap.add_argument("--seed", type=int, default=7); ap.add_argument("--key", default="A")
    ap.add_argument("--tempo", type=float, default=66); ap.add_argument("--prog", type=int, default=0)
    a = ap.parse_args()
    dry = compose(a.dur, a.seed, a.key, a.tempo, a.prog)
    ir = reverb_ir(seed=a.seed)
    sends = {"piano": 0.35, "violin": 0.55, "cello": 0.45, "strings": 0.6, "choir": 0.7, "voice": 0.6}
    mix = np.zeros_like(dry["piano"])
    wet = np.zeros_like(mix)
    for k, sig in dry.items():
        mix += sig
        wet += sig * sends[k]
    wet = np.stack([fftconvolve(wet[:, c], ir[:, c])[: len(mix)] for c in (0, 1)], axis=1)
    mix = mix * 0.8 + wet * 0.9
    n = int(a.dur * SR); mix = mix[:n]
    fi = int(0.05 * SR); fo = int(2.2 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.6
    mix /= np.max(np.abs(mix)) * 1.1
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    main()
