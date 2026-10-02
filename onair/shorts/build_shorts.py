#!/usr/bin/env python3
"""Builds the 15-second Shorts composition page: onair/shorts/out/shorts.html.

Fonts are the same official Pretendard dynamic subsets the site inlines (build.font_faces).
The multiview wall and the MAIN MC ticker come from build.py's LIVE and COURSE data.

usage: python3 onair/shorts/build_shorts.py <font-cache-dir>
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import build  # noqa: E402  (takes the font cache dir from argv[1])

OUT = HERE / "out"
# 4x4 multiview: slot 0 receives the shrinking LIVE COMMERCE title card, slot 5 is the PGM monitor the camera zooms into
WALL = [None, "fashion_2", "home_1", "travel_3", "fashion_8", "wellness_3", "wellness_1", "home_3",
        "fashion_6", "travel_2", "fashion_4", "home_2", "wellness_2", "fashion_7", "travel_1", "fashion_5"]


def main():
    live = {d["f"]: d for d in build.LIVE}
    tiles = [{"src": None, "label": None} if f is None else {"src": f"../../assets/live/{f}.jpg", "label": live[f]["brand"]} for f in WALL]
    events = [c["title"] for c in build.COURSE if c["kind"] == "cp" and not c.get("when")]
    data = json.dumps({"tiles": tiles, "events": events}, ensure_ascii=False)

    src = (HERE / "shorts_src.html").read_text()
    page = (src.replace("/*DATA*/null", data)
               .replace('src="../assets/', 'src="../../assets/')
               .replace('src="vendor/', 'src="../vendor/'))
    glyphs = page + "".join(chr(c) for c in range(0x20, 0x7F))
    faces, n = build.font_faces(glyphs)
    page = page.replace("/*FONTS*/", faces)
    OUT.mkdir(exist_ok=True)
    (OUT / "shorts.html").write_text(page)
    print(f"shorts.html {len(page) // 1024} KB · font subsets {n} · wall {len(tiles)} · ticker {len(events)}")


if __name__ == "__main__":
    main()
