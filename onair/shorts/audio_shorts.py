#!/usr/bin/env python3
"""Synthesizes the Shorts soundtrack from the composition's cue sheet (window.SHORTS.cues).

Everything is generated here (no samples): a 1 kHz line-up tone and leader beeps, a 120 BPM bed
in C major that drops out on each channel change, whooshes, impacts, TV static, AF beeps, odometer
ticks, tile flips, heart pops, a tape stop on OFF AIR and a CRT power-off. The mix is loudness
normalised to -14 LUFS with ffmpeg's two-pass loudnorm.
"""
import json, pathlib, subprocess

import numpy as np
import scipy.signal as ss
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(2026)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def noise(n):
    return rng.standard_normal(n)


def filt(x, kind, f):
    b, a = ss.butter(2, np.array(f) / (SR / 2), kind)
    return ss.lfilter(b, a, x)


def svf_band(x, fc, q=0.8):
    """Band-pass with a per-sample cutoff (Chamberlin state-variable filter)."""
    low = band = 0.0
    out = np.empty(len(x))
    fs = (2 * np.sin(np.pi * np.minimum(fc, SR / 6) / SR)).tolist()
    for i, v in enumerate(x.tolist()):
        f = fs[i]
        band += f * (v - low - q * band)
        low += f * band
        out[i] = band
    return out


# ───────── instruments ─────────
def kick(f0=160, f1=46, tau=0.16, dur=0.45, click=0.5):
    t = tt(dur)
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t / 0.032)) / SR
    return np.tanh(1.7 * (np.sin(ph) * np.exp(-t / tau) + click * noise(len(t)) * np.exp(-t / 0.003))) * 0.9


def clap(dur=0.32):
    t = tt(dur)
    e = sum((t >= d) * np.exp(-np.maximum(t - d, 0) / 0.007) for d in (0, 0.011, 0.023))
    e = e + (t >= 0.032) * np.exp(-np.maximum(t - 0.032, 0) / 0.09)
    return filt(noise(len(t)), "band", [900, 3400]) * e * 1.3


def snare(dur=0.22):
    t = tt(dur)
    return 0.6 * filt(noise(len(t)), "band", [1500, 8000]) * np.exp(-t / 0.06) + 0.35 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045)


def hat(open_=False):
    t = tt(0.32 if open_ else 0.07)
    return filt(noise(len(t)), "high", 7500) * np.exp(-t / (0.11 if open_ else 0.017)) * 0.45


def saw(f, t, K=24):
    K = max(1, min(K, int(15000 / f)))
    return sum(np.sin(2 * np.pi * k * f * t) / k for k in range(1, K + 1)) * (2 / np.pi)


def pad(notes, dur, att=0.06, rel=0.35, cutoff=1900, gain=0.5):
    t = tt(dur + rel)
    y = sum(saw(midi(m) * 2 ** (c / 1200), t) for m in notes for c in (-9, 0, 9))
    y = filt(y, "low", cutoff)
    e = np.minimum(1, t / att) * np.where(t < dur, 1.0, np.exp(-(t - dur) / (rel / 3)))
    return y * e * gain / (3 * len(notes))


def pluck(f, dur=0.22, gain=0.22):
    t = tt(dur)
    return gain * sum(np.sin(2 * np.pi * k * f * t) / k * np.exp(-t * (7 + 5 * k)) for k in range(1, 9))


def stab(notes, dur=0.34, gain=0.5):
    t = tt(dur)
    y = sum(np.sin(2 * np.pi * k * midi(m) * 2 ** (c / 1200) * t) / k * np.exp(-t * (3 + 1.7 * k))
            for m in notes for c in (-10, 10) for k in range(1, 16))
    return y * gain / (2 * len(notes))


def bass(f, dur, gain=0.42):
    t = tt(dur)
    y = np.sin(2 * np.pi * f * t) + 0.35 * np.tanh(2.5 * np.sin(2 * np.pi * f * t)) + 0.25 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.06)
    return y * np.minimum(1, t / 0.004) * np.exp(-t / (dur * 0.9)) * gain


def bell(f, dur=1.1, gain=0.22):
    t = tt(dur)
    parts = [(1, 1, 0.8), (2.0, 0.5, 0.45), (3.01, 0.35, 0.3), (4.2, 0.22, 0.2), (5.43, 0.14, 0.15)]
    return gain * sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in parts)


def beep(f=1000, dur=0.07, gain=0.3):
    t = tt(dur)
    return gain * np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.003) * np.minimum(1, (dur - t) / 0.004)


def whoosh(dur=0.36, f0=250, f1=5200, gain=0.4):
    t = tt(dur)
    p = t / dur
    fc = f0 * (f1 / f0) ** np.sin(np.pi * p * 0.85)
    y = svf_band(noise(len(t)), fc, 0.9)
    return gain * y * np.sin(np.pi * p) ** 1.6 / (np.abs(y).max() + 1e-9)


def riser(dur, gain=0.35):
    t = tt(dur)
    p = t / dur
    y = svf_band(noise(len(t)), 200 * 30 ** p, 0.6)
    y = y / (np.abs(y).max() + 1e-9)
    tone = 0.2 * np.sin(2 * np.pi * np.cumsum(220 * 4 ** p) / SR)
    return gain * (y + tone) * p ** 2.2


def crash(dur=1.0, gain=0.35):
    t = tt(dur)
    return gain * filt(noise(len(t)), "high", 4500) * np.exp(-t / 0.35)


def sub_boom(dur=1.1, gain=0.6):
    t = tt(dur)
    return gain * np.sin(2 * np.pi * np.cumsum(38 + 30 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.45)


def static(dur, gain=0.2):
    t = tt(dur)
    flick = 0.75 + 0.25 * np.sign(np.sin(2 * np.pi * 59.94 * t))
    return gain * filt(noise(len(t)), "band", [400, 7000]) * flick * np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.02)


def click(gain=0.35):
    t = tt(0.06)
    return gain * (noise(len(t)) * np.exp(-t / 0.002) + np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.02))


def tick(f=3200, gain=0.12):
    t = tt(0.03)
    return gain * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006)


def pop(f=600, gain=0.16):
    t = tt(0.07)
    return gain * np.sin(2 * np.pi * np.cumsum(f + 1600 * t / 0.07) / SR) * np.exp(-t / 0.02)


def servo(gain=0.08):
    t = tt(0.05)
    return gain * filt(noise(len(t)), "band", [1800, 4000]) * np.sin(np.pi * t / 0.05)


def shutter_click(gain=0.3):
    t = tt(0.09)
    e = np.exp(-t / 0.004) + (t > 0.045) * np.exp(-np.maximum(t - 0.045, 0) / 0.006)
    return gain * filt(noise(len(t)), "band", [1500, 9000]) * e


def zap(gain=0.4):
    t = tt(0.3)
    sw = gain * np.sin(2 * np.pi * np.cumsum(60 + 9000 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.12)
    return sw + 0.15 * filt(noise(len(t)), "high", 3000) * np.exp(-t / 0.03)


# ───────── mixing ─────────
class Bus:
    def __init__(self, dur):
        self.x = np.zeros((int(dur * SR) + SR, 2))

    def add(self, t, sig, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i < 0:
            sig, i = sig[-i:], 0
        n = min(len(sig), len(self.x) - i)
        if n <= 0:
            return
        a = (pan + 1) * np.pi / 4
        self.x[i:i + n, 0] += sig[:n] * gain * np.cos(a) * np.sqrt(2)
        self.x[i:i + n, 1] += sig[:n] * gain * np.sin(a) * np.sqrt(2)


def reverb(x, secs=1.4, mix=0.18):
    t = tt(secs)
    ir = np.stack([noise(len(t)) * np.exp(-t / 0.32), noise(len(t)) * np.exp(-t / 0.32)], 1)
    ir /= np.sqrt((ir ** 2).sum(0))
    wet = np.stack([ss.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x + mix * wet


def gate(n, holes, fade=0.012):
    g = np.ones(n)
    t = np.arange(n) / SR
    for a, b in holes:
        g = np.minimum(g, np.clip(np.maximum((a - t) / fade, (t - b) / fade), 0, 1))
    return g


CH = {"F": [53, 57, 60, 65], "G": [55, 59, 62, 67], "Am": [57, 60, 64, 69], "C": [48, 55, 60, 64, 67]}
ROOT = {"F": 41, "G": 43, "Am": 45, "C": 36}


def chord_at(t):
    for a, b, c in [(1.4, 3.4, "F"), (3.4, 5.4, "G"), (5.4, 7.4, "Am"), (7.4, 9.4, "F"), (9.4, 10.4, "Am"), (10.4, 11.4, "G"),
                    (11.4, 12.4, "F"), (12.4, 13.42, "G"), (13.42, 16, "C")]:
        if a <= t < b:
            return c
    return "F"


def music(cues, dur):
    drums, keys, low = Bus(dur), Bus(dur), Bus(dur)
    beat = 0.5
    g0 = cues["grid0"]
    kicks = []
    segs = [(1.9, 4.86, "A"), (5.4, 8.36, "B"), (8.9, 11.4, "C")]
    for a, b, kind in segs:
        k0 = int(np.ceil((a - g0) / beat - 1e-6))
        t = g0 + k0 * beat
        while t < b - 1e-6:
            kidx = round((t - g0) / beat)
            drums.add(t, kick(), 0.95); kicks.append(t)
            if kidx % 2 == 1:
                drums.add(t, clap(), 0.5, 0.05)
            c = chord_at(t)
            for s in range(4):  # sixteenths
                u = t + s * beat / 4
                if u >= b:
                    break
                if kind == "A":
                    if s == 2: drums.add(u, hat(), 0.5, 0.3)
                    if s in (0, 2): low.add(u, bass(midi(ROOT[c]), 0.22), 0.8)
                    if s % 2 == 0: keys.add(u, pluck(midi(CH[c][(kidx * 2 + s // 2) % 4] + 12)), 0.7, -0.25)
                elif kind == "B":
                    drums.add(u, hat(), 0.55 if s == 2 else 0.3, 0.3)
                    if s in (0, 2): low.add(u, bass(midi(ROOT[c] + (12 if s == 2 else 0)), 0.2), 0.85)
                    keys.add(u, pluck(midi(CH[c][(kidx * 4 + s) % 4] + 12), 0.18), 0.6, -0.3 if s % 2 else 0.3)
                else:
                    if s == 2:
                        drums.add(u, hat(open_=True), 0.35, 0.25)
                        low.add(u, bass(midi(ROOT[c]), 0.2), 0.9)
                        keys.add(u, stab([n + 12 for n in CH[c]], 0.3), 0.55)
            t += beat
    for a, b, c in [(1.4, 3.4, "F"), (3.4, 4.86, "G"), (5.4, 7.4, "Am"), (7.4, 8.36, "F"), (8.9, 9.4, "F"), (9.4, 10.4, "Am"), (10.4, 11.4, "G")]:
        keys.add(a, pad(CH[c], b - a, gain=0.42), 0.8)
    # breakdown → build → resolve
    keys.add(11.4, pad(CH["F"], 1.0, att=0.25, cutoff=1100, gain=0.55), 0.9)
    keys.add(12.4, pad(CH["G"], 1.02, att=0.1, cutoff=2400, gain=0.55), 0.9)
    for t in (11.4, 11.9, 12.4, 12.9):
        drums.add(t, kick(f0=110, f1=42, tau=0.12, click=0.1), 0.6); kicks.append(t)
    roll = [12.9 + i * 0.125 for i in range(2)] + [13.15 + i * 0.0625 for i in range(4)]
    for i, t in enumerate(roll):
        drums.add(t, snare(), 0.18 + 0.05 * i, 0.1)
    keys.add(13.42, pad(CH["C"], 1.2, att=0.02, cutoff=2600, gain=0.6), 0.95)
    keys.add(13.42, stab([n + 12 for n in CH["C"]], 0.5), 0.8)
    low.add(13.42, bass(midi(36), 0.9, 0.5), 1.0)
    for t in (13.42, 13.92):
        drums.add(t, kick(), 0.9); kicks.append(t)
    # sidechain duck on keys and bass
    n = len(keys.x)
    tg = np.arange(n) / SR
    duck = np.ones(n)
    for k in kicks:
        m = tg >= k
        duck[m] = np.minimum(duck[m], 1 - 0.55 * np.exp(-(tg[m] - k) / 0.11))
    mix = drums.x + reverb(keys.x, mix=0.22) * duck[:, None] + low.x * duck[:, None]
    mix *= gate(n, cues["static"])[:, None]
    return mix


def tape_stop(x, t0, dur=0.26):
    """Slow the bed to a halt from t0 (reads the buffer at a falling rate)."""
    i0 = int(t0 * SR)
    m = int(dur * SR)
    speed = (1 - np.arange(m) / m) ** 1.5
    pos = i0 + np.cumsum(speed)
    out = x.copy()
    for c in range(2):
        out[i0:i0 + m, c] = np.interp(pos, np.arange(len(x)), x[:, c]) * np.linspace(1, 0.4, m)
    out[i0 + m:] = 0
    return out


def sfx(cues, dur):
    fx = Bus(dur)
    fx.add(0.0, beep(1000, 0.36, 0.16), 1.0)                                     # line-up tone under the bars
    fx.add(cues["clap"], shutter_click(0.5), 1.0); fx.add(cues["clap"], click(0.25), 1.0)  # slate clap
    for t in cues["beeps"]:
        fx.add(t, beep(1000, 0.07, 0.3), 1.0)                                    # 3 · 2 · 1
    fx.add(0.5, riser(0.9, 0.3), 1.0)
    s = cues["slam"]                                                             # ON AIR
    fx.add(s, kick(200, 40, 0.3, 0.9, 0.8), 1.0); fx.add(s, sub_boom(), 0.9); fx.add(s, crash(1.3), 0.9)
    fx.add(s, stab([n + 12 for n in CH["F"]], 0.6), 0.9)
    for t in cues["whoosh"]:
        fx.add(t, whoosh(), 0.9, float(rng.uniform(-0.3, 0.3)))
    for t in cues["af"]:
        fx.add(t, servo(), 1.0, 0.2)                                             # AF hunting
    fx.add(cues["lock"] - 0.05, beep(2900, 0.045, 0.22), 1.0); fx.add(cues["lock"] + 0.03, beep(2900, 0.045, 0.22), 1.0)
    fx.add(cues["nameHit"], shutter_click(0.4), 1.0)
    fx.add(cues["nameHit"], kick(150, 50, 0.14, 0.4, 0.6), 0.7); fx.add(cues["nameHit"], crash(0.6, 0.18), 1.0)
    for i, t in enumerate(cues["roles"]):
        fx.add(t, pluck(midi(84 + 2 * i), 0.16, 0.25), 0.8, 0.2)
    for a, b in cues["static"]:
        fx.add(a, click(0.4), 1.0); fx.add(a, static(b - a), 1.0); fx.add(b - 0.05, click(0.3), 1.0)
    for t in cues["cards"]:
        fx.add(t, kick(170, 55, 0.1, 0.3, 0.7), 0.6); fx.add(t, snare(), 0.35, 0.15)
    a, b = cues["odo"]                                                           # odometer: a tick per 400 counted
    ts = np.linspace(a, b, 4000)
    v = 12000 * (1 - (1 - (ts - a) / (b - a)) ** 4)
    for t in ts[1:][np.diff(np.floor(v / 400)) > 0]:
        fx.add(float(t), tick(2600, 0.1), 1.0, 0.1)
    fx.add(b, bell(midi(88), 0.9, 0.2), 1.0)
    for i, t in enumerate(cues["flips"]):
        fx.add(t, tick(1800 + 90 * i, 0.07), 1.0, -0.6 + 0.08 * i)
    fx.add(cues["take"], click(0.45), 1.0); fx.add(cues["take"], tick(1200, 0.15), 1.0)
    for i, t in enumerate(cues["hearts"]):
        fx.add(t, pop(500 + 70 * (i % 5), 0.1), 1.0, 0.5)
    for t in cues["lines"]:
        fx.add(t, tick(1500, 0.12), 1.0)
    fx.add(12.6, riser(0.82, 0.32), 1.0)
    for i in range(10):
        fx.add(cues["shutter"] + i * 0.016, tick(900 + 60 * i, 0.08), 1.0, -0.5 if i % 2 else 0.5)
    fx.add(13.42, crash(1.2, 0.3), 1.0); fx.add(13.42, sub_boom(0.9, 0.4), 1.0)
    fx.add(cues["land"], kick(120, 45, 0.12, 0.35, 0.4), 0.55); fx.add(cues["land"] + 0.01, bell(3200, 0.25, 0.05), 1.0)
    for i, m in enumerate((84, 88, 91, 96)):
        fx.add(cues["sparkle"] + 0.06 * i, bell(midi(m), 0.8, 0.09), 1.0, -0.4 + 0.27 * i)
    fx.add(cues["off"], click(0.5), 1.0)
    fx.add(cues["crt"], zap(0.35), 1.0); fx.add(cues["crt"] + 0.25, click(0.25), 1.0)
    return reverb(fx.x, 1.0, 0.1)


def render(cues, dur, path):
    path = pathlib.Path(path)
    bed = tape_stop(music(cues, dur), cues["off"])
    x = 0.62 * bed + 0.85 * sfx(cues, dur)
    x = x[: int(dur * SR)]
    x = np.tanh(1.2 * x) / np.tanh(1.2)
    x *= 0.89 / (np.abs(x).max() + 1e-9)
    raw = path.with_name("audio_raw.wav")
    wavfile.write(raw, SR, (x * 32767).astype(np.int16))
    # two-pass loudnorm to -14 LUFS (platform target), true peak -1.5 dBTP
    p1 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    m = json.loads(p1[p1.rindex("{"):p1.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", af, "-ar", str(SR), str(path)], check=True)
    print(f"audio → {path} (input {m['input_i']} LUFS → -14)")
    return path


if __name__ == "__main__":
    import sys
    cues = json.loads(pathlib.Path(sys.argv[1]).read_text())
    render(cues, 15.0, sys.argv[2])
