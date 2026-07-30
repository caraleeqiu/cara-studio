#!/usr/bin/env python3
"""
出音乐。用法：
    python3 tools/music.py            出全部三首
    python3 tools/music.py night      只出一首
    python3 tools/music.py --list     看有哪些

用 Google 的 Lyria 3。key 从 .env 读，和出图共用。
文件存到 assets/audio/<名字>.mp3，前端会自动接上。
"""

import base64, json, os, sys, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "audio"
MODEL = "lyria-3-pro-preview"          # clip 版更短更快，pro 版长一些
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}"

# 三首对应界面上的三个音乐档位。
# 共用的底子：同一间放映厅、同一台老放映机、同一个深夜。
ROOM = (
    "Instrumental only, no vocals, no lyrics. Recorded as if in a small room: "
    "audible room tone, faint tape hiss and vinyl crackle, nothing polished or synthetic. "
    "Slow tempo, generous space between notes, loops cleanly with no hard ending."
)

TRACKS = {
    # 界面标签：Night Shift · SLOW · WARM
    "night": (
        "Warm late-night lo-fi for a tiny cinema that one person runs alone. "
        "Soft electric piano playing simple chords, brushed drums kept very low, "
        "upright bass walking gently underneath. Cosy, unhurried, a little melancholy. "
        "The feeling of tidying up after the last screening."
    ),
    # 界面标签：Neon Aisle · LIGHT · STEADY
    "neon": (
        "Light lo-fi with a steady pulse, a shade brighter than the others. "
        "Muted electric guitar figures, warm analogue synth pad, soft rimshot rhythm, "
        "a little shuffle in the groove. Calm but awake. "
        "The feeling of walking a lit aisle with the projector already running."
    ),
    # 界面标签：Reel Room · COOL · QUIET
    "reel": (
        "Quiet ambient, cooler and sparser than the others. Long sustained pads, "
        "occasional single piano notes with lots of decay, almost no percussion, "
        "the faint mechanical rhythm of a film projector far off. "
        "Still, spacious, slightly cold. The feeling of the empty room after everyone leaves."
    ),
}


def load_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY", "")


def generate(name):
    prompt = f"{TRACKS[name]}\n\n{ROOM}"
    req = urllib.request.Request(
        API.format(MODEL, load_key()),
        data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.load(r)

    cands = data.get("candidates") or []
    if not cands:
        raise RuntimeError("no candidates: " + json.dumps(data)[:300])
    cand = cands[0]
    # 没有 content 时通常是被安全策略挡了，finishReason 会说明原因
    if "content" not in cand:
        raise RuntimeError(f"finishReason={cand.get('finishReason')} "
                           f"safety={json.dumps(cand.get('safetyRatings', []))[:200]}")
    for part in cand["content"].get("parts", []):
        blob = part.get("inlineData") or part.get("inline_data")
        if blob:
            OUT.mkdir(parents=True, exist_ok=True)
            path = OUT / f"{name}.mp3"
            path.write_bytes(base64.b64decode(blob["data"]))
            return path
    raise RuntimeError("no audio part: " + json.dumps(cand)[:300])


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--list":
        for k in TRACKS: print(" ", k)
        sys.exit()
    names = [a for a in args if a in TRACKS] or list(TRACKS)
    for n in names:
        for attempt in (1, 2):
            try:
                p = generate(n)
                print(f"✓ {n} → {p.relative_to(ROOT)} ({p.stat().st_size // 1024} KB)")
                break
            except Exception as e:
                if attempt == 1:
                    print(f"  {n}: retrying ({e})")
                else:
                    print(f"✗ {n}: {e}")
