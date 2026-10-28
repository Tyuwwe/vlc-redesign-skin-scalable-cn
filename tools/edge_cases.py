"""Screenshots of edge cases to look over: the player at its smallest size, a very long
multilingual title and filename, and a playlist long enough to scroll. Needs the media from
tools/make_testmedia.py.

    python tools/edge_cases.py
    python tools/edge_cases.py --scale 2
    python tools/edge_cases.py --language zh-CN
"""
import argparse
import base64
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_test as T  # noqa: E402
from run_skin import user32  # noqa: E402

LONG = T.ROOT / "testmedia" / "简体中文＿繁體中文＿English（全角標點：測試！）.mp4"
LONG_TITLE = ("简体中文：漫长的旅程（导演剪辑版），繁體中文：漫長的旅程【修復版】"
              "＿English: The Long Journey, Part Two?!")


def http(v, query):
    auth = base64.b64encode(f":{T.HTTP_PASSWORD}".encode()).decode()
    url = f"http://127.0.0.1:{T.HTTP_PORT}/requests/status.json?{query}"
    urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"}), timeout=5).read()


def enqueue(v, path):
    http(v, "command=in_enqueue&input=" + urllib.parse.quote(Path(path).resolve().as_uri()))


def drag(v, x0, y0, x1, y1):
    """Press and release at logical window coordinates, by posted messages."""
    hwnd = v.main()[0]
    x0, y0 = T.point(x0, y0)
    x1, y1 = T.point(x1, y1)
    for msg, wp, x, y in ((0x200, 0, x0, y0), (0x201, 1, x0, y0), (0x200, 1, (x0 + x1) // 2, (y0 + y1) // 2),
                          (0x200, 1, x1, y1), (0x202, 0, x1, y1)):
        user32.PostMessageW(hwnd, msg, wp, (y << 16) | (x & 0xFFFF))
        time.sleep(0.25)
    time.sleep(0.8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, choices=(1, 2), default=1)
    ap.add_argument("--language", choices=("en", "zh-CN"), default="en")
    a = ap.parse_args()
    T.set_scale(a.scale, a.language)
    T.SHOTS.mkdir(parents=True, exist_ok=True)
    if not LONG.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(T.VIDEO), "-c", "copy",
                        "-metadata", f"title={LONG_TITLE}", str(LONG)], check=True)
    for start in ("dark_full", "dark_side", "dark_mini"):
        T.build(start)
        v = T.Vlc(f"edge-{start}", (LONG,))
        v.wait(lambda s: s.get("state") == "playing" and s.get("position", 0) > 0, 15)
        time.sleep(1.5)                            # let the video window and times appear
        if start == "dark_side":
            for _ in range(30):
                enqueue(v, T.MUSIC)
            time.sleep(1)
        w, h = v.size()
        v.shot("default")
        if not start.endswith("mini"):
            drag(v, w / T.SCALE - 6, h / T.SCALE - 6, 10, 10)  # resize corner past the minimum
            print(f"{start}: dragged the corner from {w} x {h}; now {v.size()}")
            time.sleep(1)
            v.shot("smallest")
            v.shot("smallest-later")               # a moment later: a long title scrolls
        v.close()
    T.build("dark_full")
    print(f"screenshots in {T.SHOTS}")


if __name__ == "__main__":
    main()
