#!/usr/bin/env python3
"""Renders the Shorts composition by seeking it frame by frame (window.renderAt) in headless Chromium.

Fast moves get real motion blur (several sub-frame samples averaged inside the shutter window
listed in window.SHORTS.blur); channel changes get an RGB-split / slice glitch (window.SHORTS.glitch).

usage:
  render_shorts.py stills <t> [<t> ...]      → out/stills/*.png and out/stills/sheet.jpg
  render_shorts.py video [--fps 60] [--crf 16] → out/onair_shorts.mp4 (audio from audio_shorts.py)
Needs Playwright's Chromium (PLAYWRIGHT_BROWSERS_PATH), numpy, opencv and ffmpeg.
"""
import argparse, asyncio, json, pathlib, subprocess, sys, time

import cv2
import numpy as np
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
PAGE = OUT / "shorts.html"
W, H = 1080, 1920


def glitch(img, amp, seed):
    rng = np.random.default_rng(seed)
    out = img.copy()
    dx = max(1, int(26 * amp))
    out[:, :, 2] = np.roll(img[:, :, 2], dx, axis=1)
    out[:, :, 0] = np.roll(img[:, :, 0], -dx, axis=1)
    for _ in range(int(5 + 12 * amp)):
        y, h = int(rng.integers(0, H - 8)), int(rng.integers(6, 140))
        out[y:y + h] = np.roll(out[y:y + h], int(rng.normal(0, 90 * amp)), axis=1)
    return out


def samples_at(t, fps, windows):
    n, shutter = 1, 0.0
    for t0, t1, k, s in windows:
        if t0 <= t < t1 and k > n:
            n, shutter = k, s
    if n == 1:
        return [t]
    span = shutter / fps
    return [t - span / 2 + span * (i + 0.5) / n for i in range(n)]


async def open_page(p):
    b = await p.chromium.launch(args=["--force-color-profile=srgb", "--font-render-hinting=none", "--hide-scrollbars"])
    pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    await pg.goto(PAGE.as_uri(), wait_until="load")
    await pg.wait_for_function("window.SHORTS_READY === true", timeout=30000)
    return b, pg, errs


async def grab(pg, t):
    await pg.evaluate("t => window.renderAt(t)", t)
    buf = await pg.screenshot(type="jpeg", quality=95)
    return cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR)


async def frame(pg, t, fps, meta, idx):
    ts = samples_at(t, fps, meta["blur"])
    if len(ts) == 1:
        img = await grab(pg, ts[0])
    else:
        acc = np.zeros((H, W, 3), np.float32)
        for u in ts:
            acc += await grab(pg, u)
        img = (acc / len(ts) + 0.5).astype(np.uint8)
    for t0, t1, amp in meta["glitch"]:
        if t0 <= t < t1:
            img = glitch(img, amp * np.sin(np.pi * (t - t0) / (t1 - t0)) + 0.15, idx)
    return img


async def stills(times):
    d = OUT / "stills"
    d.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b, pg, errs = await open_page(p)
        meta = await pg.evaluate("window.SHORTS")
        thumbs = []
        for i, t in enumerate(sorted(times)):
            img = await frame(pg, t, meta["fps"], meta, int(t * meta["fps"]))
            cv2.imwrite(str(d / f"t_{t:05.2f}.png"), img)
            th = cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA)
            cv2.putText(th, f"{t:.2f}", (8, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 4)
            cv2.putText(th, f"{t:.2f}", (8, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 1)
            thumbs.append(th)
        await b.close()
    cols = 6
    while len(thumbs) % cols:
        thumbs.append(np.zeros_like(thumbs[0]))
    rows = [np.hstack(thumbs[i:i + cols]) for i in range(0, len(thumbs), cols)]
    cv2.imwrite(str(d / "sheet.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("stills →", d, "| page errors:", errs or "none")


async def video(fps, crf):
    import audio_shorts
    async with async_playwright() as p:
        b, pg, errs = await open_page(p)
        meta = await pg.evaluate("window.SHORTS")
        (OUT / "cues.json").write_text(json.dumps(meta["cues"], indent=1))
        wav = audio_shorts.render(meta["cues"], meta["duration"], OUT / "audio.wav")
        n = int(round(meta["duration"] * fps))
        mp4 = OUT / "onair_shorts.mp4"
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
            "-i", str(wav),
            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-level", "4.2",
            "-maxrate", "40M", "-bufsize", "80M",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(mp4)],
            stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(n):
            img = await frame(pg, i / fps, fps, meta, i)
            ff.stdin.write(img.tobytes())
            if i % 60 == 0:
                print(f"  frame {i}/{n}  {time.time() - t0:5.1f}s", flush=True)
        ff.stdin.close()
        ff.wait()
        await b.close()
    print(f"video → {mp4}  ({mp4.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f}s) | page errors:", errs or "none")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["stills", "video"])
    ap.add_argument("times", nargs="*", type=float)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    sys.path.insert(0, str(HERE))
    asyncio.run(stills(a.times) if a.mode == "stills" else video(a.fps, a.crf))


if __name__ == "__main__":
    main()
