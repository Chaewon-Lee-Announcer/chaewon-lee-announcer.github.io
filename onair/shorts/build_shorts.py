#!/usr/bin/env python3
"""Builds the ON AIR Shorts in four lengths: onair/shorts/out/shorts_{15,30,45,60}.html.

Each page plays a PLAN — a list of scene modules (intro, ON AIR slam, hero, channel changes, content
channels, prompter, end card) with start times and hold lengths. The 15-second plan is the original
cut; longer cuts add channels (RACE DAY, MOTORSPORTS, ON TV, VOD, ON STAGE, RECORD, CAM 2, WORKED WITH)
and spread the remaining time over holds so every length lands exactly. Every fact comes from
build.py's data; anything dated after today is left out (a video cannot update itself).

usage: python3 onair/shorts/build_shorts.py <font-cache-dir>
"""
import datetime, html, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import build  # noqa: E402  (takes the font cache dir from argv[1])

OUT = HERE / "out"
SITE = "chaewon-lee-announcer.github.io"
LIVE_IMG = "../../assets/live/"
# 4x4 multiview: slot 0 receives the shrinking LIVE COMMERCE title card, slot 5 is the PGM monitor the camera zooms into
WALL = [None, "fashion_2", "home_1", "travel_3", "fashion_8", "wellness_3", "wellness_1", "home_3",
        "fashion_6", "travel_2", "fashion_4", "home_2", "wellness_2", "fashion_7", "travel_1", "fashion_5"]

LABEL = {"sports": "Sports", "race": "Race Day", "pit": "Motorsports", "tv": "On TV", "stage": "On Stage", "cam2": "Cam 2", "live": "Live"}
SWIPE_IN = {"score", "vod", "brands", "prompter"}          # these enter by a vertical swipe instead of a channel change
ORDER = {
    15: ["sports", "live"],
    30: ["sports", "race", "tv", "stage", "live"],
    45: ["sports", "race", "pit", "tv", "stage", "score", "cam2", "live"],
    60: ["sports", "race", "pit", "tv", "vod", "stage", "score", "cam2", "live", "brands"],
}
BASE = {"race": 3.0, "tv": 3.0, "stage": 2.9, "pit": 3.0, "cam2": 2.8, "score": 2.2, "vod": 2.6, "brands": 2.2}
WEIGHT = {"hero": 1.0, "sports": 1.1, "live": 1.0, "end": 0.8, "prompter": 0.7,
          "race": 1.1, "tv": 1.1, "stage": 1.1, "pit": 1.0, "cam2": 0.9, "score": 0.7, "vod": 0.8, "brands": 0.7}
CAP = {"hero": 1.2, "sports": 1.6, "live": 1.4, "end": 1.6, "prompter": 1.0}   # new channels: up to 2.6 s extra each


def period_key(p):
    """Newest-first key for period strings such as '2026.01', '2024—2026', '2024.04'."""
    years = [int(y) for y in re.findall(r"\d{4}", p)]
    month = re.search(r"\d{4}\.(\d{2})(?!.*\d{4})", p)
    return (max(years) if years else 0, int(month.group(1)) if month else 0)


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def data():
    today = datetime.date.today().isoformat()
    cps = [c for c in build.COURSE if c["kind"] == "cp" and not (c.get("when") and c["when"] >= today)]
    titles = {c["title"] for c in cps}
    race = ["화천 DMZ 랠리", "설악그란폰도", "철원 DMZ 국제평화마라톤", "손기정 평화마라톤", "양양 강변 전국 마라톤"]
    assert all(r in titles for r in race), "race checkpoints must exist in COURSE"
    live = {d["f"]: d for d in build.LIVE}
    corp = {t: (d, t, r) for d, t, r in build.CORPORATE + build.RECREATION}
    stage = ["타린로즈 VIP 고객 초청행사", "크립토닷컴 코리아 런칭파티", "삼성 멤버스 스타즈 발대식", "현대자동차 아이디어 페스티벌",
             "BMW M클럽 코리아 신년회", "캐치! 티니핑 전국 싱어롱쇼"]
    score = [(int(n), text(lbl)) for n, lbl in re.findall(r'data-to="(\d+)">[\d,]+</div><p>([^<]+)', build.score())]
    pit = build.pit()
    prof = dict(re.findall(r'<dt class="mono">([A-Z]+)</dt><dd>([^<]+)</dd>', build.profile()))
    return {
        "tiles": [{"src": None, "label": None} if f is None else {"src": f"{LIVE_IMG}{f}.jpg", "label": live[f]["brand"]} for f in WALL],
        "events": [c["title"] for c in cps],
        "race": {"cps": [{"name": "START LINE", "sub": "Start · 0.000 KM", "flag": True}]
                 + [{"name": n, "sub": f"CP {i + 1:02d}"} for i, n in enumerate(race)]
                 + [{"name": "FINISH", "sub": "Finish · 42.195 KM", "flag": True}],
                 "foot1": "마라톤 · 그란폰도 · 랠리 메인 MC", "foot2": f"Season {build.SEASON}"},
        "tv": [{k: t[k] for k in ("ch", "date", "title", "role", "bg")} for t in build.TV],
        "stage": [dict(zip(("date", "title", "role"), corp[t])) for t in stage],
        "score": [{"n": n, "label": lbl} for n, lbl in score if n < 1000],
        "pit": {"quote": "“" + text(re.search(r"<blockquote>(.*?)</blockquote>", pit).group(1)) + "”",
                "cite": text(re.search(r'<cite class="mono">(.*?)</cite>', pit).group(1)),
                "items": [[text(t), text(d)] for t, d in re.findall(r'<li><b>(.*?)</b><span class="mono">(.*?)</span></li>', pit)]},
        "fitting": [[k, prof[k].replace(" · ", "\u00a0· ")] for k in ("HEIGHT", "TOP", "BOTTOM", "SHOES", "FIELD")],  # a wrap falls after a dot, never before it
        "brandsA": build.BRANDS_A, "brandsB": build.BRANDS_B, "brandsFoot": "+ " + " · ".join(build.MORE_AIR[:3]),
        "yt": [{"src": "../../" + v["thumb"], "title": v["title"], "dur": v["dur"]} for v in build.YOUTUBE],
        "site": SITE,
    }


def assemble(length, X, D):
    """Scene list for one length; X = extra seconds per hold. Rules reproduce the original cut's overlaps."""
    seq = ORDER[length]
    scenes = [dict(mod="intro", t0=0.0, d=1.4), dict(mod="slam", t0=1.4, d=0.6)]
    hero = dict(mod="hero", t0=1.72, h=X["hero"], d=3.23 + X["hero"])
    scenes.append(hero)
    prev, n = hero, 0
    for i, mod in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < len(seq) else "prompter"
        if mod in SWIPE_IN:
            t0, enter = prev["t0"] + prev["d"] - 0.27, "swipe"
        else:
            n += 1
            ch = dict(mod="channel", t0=prev["t0"] + prev["d"] - (0.21 if prev["mod"] == "hero" else 0.19), d=0.88,
                      n=n, label=LABEL[mod], win=0.20 if prev["mod"] == "hero" else 0.18)
            scenes.append(ch)
            t0, enter = ch["t0"] + 0.56, "channel"
        sc = dict(mod=mod, t0=t0, enter=enter, exit="swipe" if nxt in SWIPE_IN else "whip", n=n)
        if mod == "sports":
            sc.update(h=X["sports"], d=3.13 + X["sports"])
        elif mod == "live":
            sc.update(h=X["live"], d=2.67 + X["live"])
        else:
            sc["d"] = BASE[mod] + X[mod]
        if mod == "tv":
            sc["slides"] = max(3, min(5, int((sc["d"] - 0.85) / 0.7)))
        if mod == "stage":
            sc["cards"] = max(4, min(6, int((sc["d"] - 1.3) / 0.42)))
        scenes.append(sc)
        prev = sc
    p = X["prompter"]
    step = 0.38 + min(p, 0.7) * 0.12
    hold = p - 5 * (step - 0.38)
    pr = dict(mod="prompter", t0=prev["t0"] + prev["d"] - 0.27, d=2.28 + 5 * (step - 0.38) + hold, step=step, hold=hold, enter="swipe")
    scenes.append(pr)
    end = dict(mod="end", t0=pr["t0"] + pr["d"] - 0.26, h=X["end"], d=1.78 + X["end"])
    scenes.append(end)
    return scenes, end["t0"] + end["d"]


def solve(length, D):
    keys = ["hero", "sports", "live", "end", "prompter"] + [m for m in ORDER[length] if m in BASE]
    X = {k: 0.0 for k in WEIGHT}
    _, base = assemble(length, X, D)
    left, free = length - base, set(keys) if length > 15 else set()
    while left > 1e-9 and free:  # water-filling: share by weight, freeze holds that reach their cap
        w = sum(WEIGHT[k] for k in free)
        give = {k: left * WEIGHT[k] / w for k in free}
        for k in list(free):
            room = CAP.get(k, 2.6) - X[k]
            take = min(give[k], room)
            X[k] += take
            left -= take
            if take >= room - 1e-9:
                free.discard(k)
    X["end"] += left  # anything a cap left over lands on the end card
    scenes, total = assemble(length, X, D)
    assert abs(total - length) < 1e-6, (length, total)
    return scenes, X


def main():
    D = data()
    src = (HERE / "shorts_src.html").read_text()
    OUT.mkdir(exist_ok=True)
    for length in (15, 30, 45, 60):
        scenes, X = solve(length, D)
        d = json.loads(json.dumps(D))
        for s in scenes:
            if s["mod"] == "stage":  # the first cards are the directive's four, extra ones join and all sort newest first
                d["stage"] = sorted(D["stage"][: s["cards"]], key=lambda c: period_key(c["date"]), reverse=True)
        for s in scenes:
            for k, v in list(s.items()):
                if isinstance(v, float):
                    s[k] = round(v, 4)
        plan = {"length": length, "fps": 60, "scenes": scenes, "data": d}
        page = (src.replace("/*PLAN*/null", json.dumps(plan, ensure_ascii=False))
                   .replace('src="../assets/', 'src="../../assets/')
                   .replace('src="vendor/', 'src="../vendor/'))
        faces, nf = build.font_faces(page + "".join(chr(c) for c in range(0x20, 0x7F)) + "“”·—")
        page = page.replace("/*FONTS*/", faces)
        (OUT / f"shorts_{length}.html").write_text(page)
        mods = " ".join(s["mod"] if s["mod"] != "channel" else f"CH{s['n']:02d}" for s in scenes)
        holds = ", ".join(f"{k} +{v:.2f}" for k, v in X.items() if v > 0.005)
        print(f"{length:>2}s · {len(scenes)} scenes · fonts {nf} · {mods}\n     holds: {holds or 'none (original cut)'}")


if __name__ == "__main__":
    main()
