#!/usr/bin/env python3
"""
出图。用法：
    python3 tools/gen.py --list                    看有哪些镜头
    python3 tools/gen.py hall                      出一张
    python3 tools/gen.py hall --n 3                出 3 个变体（挑图用）
    python3 tools/gen.py lobby --ref assets/screening/hall.jpg
                                                   拿定好的关键图当垫图，保证同一个世界

key 从 .env 读。图存到 assets/screening/<名字>.jpg
"""

import base64, json, os, sys, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "screening"
MODEL = "gemini-3-pro-image"
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}"

# ---------------------------------------------------------------- STYLE BIBLE
# 这段决定全站气质。所有图共用，改它 = 换一个世界。
# 画法 —— 所有图共用。只管怎么画，不管画什么。
LOOK = (
    "Highly detailed anime painting in the manner of premium animated-film background art. "
    "Painterly rendering with soft brushwork and NO hard black outlines, rich volumetric lighting, "
    "cinematic depth of field, warm bloom and light haze, visible dust motes, subtle grain, "
    "layered atmospheric depth. Photographic composition and lens feel, hand-painted surfaces. "
    "Healing / lo-fi night mood. Soft rounded shapes, gentle contrast, nothing harsh or sterile. "
    "Palette: honey amber #e8b06a, warm peach #d99a7e, soft mint #8fc7bb, deep indigo night #14161f. "
    "Absolutely no text, no lettering, no signage, no subtitles, no titles, no credits, "
    "no logos, no watermark, no UI overlay."
)

# 题材 —— 只有房间图用。海报不继承这段，否则模型会一直画房间。
ROOM = (
    " Subject: a tiny private screening room that one person runs alone, late at night. "
    "Lighting is warm and inviting: honey-amber practical lamps and string lights as the key, "
    "a soft mint-teal glow from the screen as the cool accent, warm light pooling on wooden floors. "
    "Densely lived-in detail: trailing potted plants, stacked film reels, mismatched mugs, "
    "a knitted blanket over a seat, paperbacks, a small cat curled up asleep, fairy lights, "
    "a window with a blurred blue night city beyond."
)

# 项目封面的画风 —— 和房间不同。房间是相框，海报是电影。
COVER_LOOK = (
    "Gritty American rock photography, shot on 35mm push-processed film. "
    "High contrast, deep blacks, blown highlights, heavy grain, halation around the lights, "
    "slight motion blur. Raw and unpolished — press-photo energy, not illustration. "
    "Saturated crimson and magenta stage light against near-black; one cold white flash. "
    "Absolutely no text, no lettering, no signage, no logos, no watermark."
)

# 唯美对称画法（维斯·安德森那一挂）：正面平拍、绝对对称、糖果色、玩偶屋细节。
CINEMA_LOOK = (
    "Perfectly symmetrical, dead-centre, flat frontal composition shot straight on with no "
    "perspective skew, as if the wall were parallel to the film plane. Meticulous doll's-house "
    "detail, every object deliberately placed and evenly spaced. "
    "Pastel storybook palette: dusty rose, mustard yellow, powder blue, mint, warm cream, "
    "soft coral. Flat even lighting, almost no shadow, gentle film grain, slightly faded stock. "
    "Whimsical, precise, deadpan, quietly charming. Vintage props and rounded retro forms. "
    "Absolutely no text, no lettering, no signage, no logos, no watermark."
)
CINEMA_COVERS = {"poster-mvland"}

# 宏大空灵画法：巨大、空、雾、单色、渺小的光。用于 iLands。
SUBLIME_LOOK = (
    "Monumental cinematic still, large format, vast negative space and extreme minimalism. "
    "Heavy atmospheric haze and volumetric light, a single dominant colour wash across the whole "
    "frame, very low contrast in the shadows, soft grain, almost no clutter. "
    "Sublime, still, quietly awe-inducing, dreamlike scale. "
    "Absolutely no text, no lettering, no signage, no logos, no watermark."
)
SUBLIME_COVERS = set()

# 暖调画意：柔和、亲近、有人味。用于社区类项目。
WARM_LOOK = (
    "Warm painterly cinematic still, soft natural rendering, gentle film grain. "
    "Lit almost entirely by one low practical lamp: deep honey-amber pooling on the subjects, "
    "everything else falling into soft brown darkness. No coloured stage lights, no neon. "
    "Quiet, companionable, intimate, faintly storybook. Muted warm palette only. "
    "Absolutely no text, no lettering, no signage, no logos, no watermark."
)
WARM_COVERS = {"poster-ilands", "poster-vmake"}

# 技术冷调：屏幕自发光、干净、克制。用于工具类项目。
TECH_LOOK = (
    "Clean modern technical photograph, shot in a dark studio. The only light comes from the "
    "screens themselves: cool white and pale amber screen-glow against near-black. "
    "Crisp, ordered, slightly clinical, faint atmospheric haze, subtle grain. "
    "No warm lamps, no cosy furniture, no people talking, no domestic setting. "
    "Absolutely no readable text, no lettering, no logos, no watermark, no UI labels."
)
TECH_COVERS = {"poster-creative", "poster-roboneo", "poster-actionway"}
BRIGHT_COVERS = {"poster-99", "poster-didi-mx", "poster-didi-au"}

# 明亮商业广告调：日光、饱和、干净。用于消费品牌类项目。
BRIGHT_LOOK = (
    "Bright commercial advertising photograph shot in full daylight. Clean, high-key, saturated "
    "but natural colour, crisp shadows, sharp focus, no grain, no haze, no moody darkness. "
    "Optimistic and friendly, the look of a brand campaign. "
    "Absolutely no text, no lettering, no signage, no logos, no watermark."
)

# 海报专用框架 —— 单幅竖版，不是房间，不是分格。
POSTER = (
    " This is a SINGLE horizontal 16:9 key image — one unified picture filling the whole frame. "
    "NOT split panels, NOT a collage, NOT a diptych, NOT a grid, NOT a poster on a wall. "
    "Composition: the subject sits right-of-centre, leaving generous darker space across the "
    "LOWER LEFT for titling. Faint print grain."
)

# 空镜专用（房间图不要出现人）
EMPTY = " Nobody in frame. No people, no human figures."

# ---------------------------------------------------------------- 角色设定
# 和 style bible 同等重要 —— 没有这段，每张图里的人都不是同一个人。
# 定好后先出 char 参考图，之后所有含人的图都用 --ref 指向它。
CHARACTER = (
    "THE CHARACTER — always the same person, keep her consistent: "
    "a woman in her late twenties. Long dark hair worn loose, with several thin braids woven "
    "through it and one faded teal-dyed streak. Slightly undercut on one side. "
    "Rebellious, softly punk styling: an oversized worn band tee or a cropped leather jacket over it, "
    "a stack of silver ear cuffs and small studs, a couple of thin chain necklaces, "
    "black nail polish, chunky boots, a few woven bracelets. "
    "Posture is relaxed and a little slouchy — self-possessed, never posed or cute. "
    "Expression is calm and warm; the edge is in the styling, not in a scowl. "
    "Drawn in the same warm painterly anime style as the room, lit by the same practical lamps."
)

SHOTS = {
    # ---------- 关键图：放映厅（中枢） ----------
    # 构图要求：左侧、右侧、正下方各留一块可读区域挂热点，中间别太满。
    "hall": (
        "INTERIOR wide shot from the back of a tiny cosy screening room, camera at seated eye level, "
        "looking down the room toward the screen. "
        "CENTRE: the screen glows soft mint, blank, washing gentle light over everything; "
        "two short rows of comfy armchairs with knitted blankets in the lower foreground. "
        "LEFT of frame: a warm wooden shelf stacked with film reels and canisters, trailing plants "
        "spilling off it, a small lamp glowing among them. "
        "RIGHT of frame: a snug alcove with a soft sofa where {char} sits sideways, one leg tucked up, "
        "holding a warm mug in both hands, turned slightly toward the viewer — relaxed, mid-evening, "
        "as if she'd happily talk if you came over. A cat asleep on the cushion beside her. "
        "A low table with a second steaming mug. A big paper lantern glowing honey-amber above her. "
        "She is small in frame — this is a room shot, not a portrait — but clearly readable. "
        "LOWER CENTRE: a small wooden stand holding an open notebook, a little brass lamp on it. "
        "Composition is wide and calm, with clear breathing room around each of those three elements."
    ),

    "hall-b": (
        "INTERIOR wide shot from the FRONT of a tiny cinema, camera beside the screen, "
        "looking back up at the empty seating and the projection window. "
        "The projector beam comes straight at camera through heavy dust, flaring. "
        "LEFT: shelving of film reels and canisters under a work lamp. "
        "RIGHT: a small bar corner with a leather banquette and one warm lamp. "
        "LOWER CENTRE: a lectern with an open guest book and a brass lamp. "
        "Rows of empty burgundy velvet seats fill the middle ground. "
        "Wide, symmetrical, calm. Nobody in frame."
    ),

    "hall-c": (
        "INTERIOR wide three-quarter shot of a tiny cosy screening room seen from a corner, "
        "so the glowing blank screen is on the LEFT and the room opens warmly to the RIGHT. "
        "A soft projector beam crosses the frame diagonally through floating dust. "
        "FAR LEFT: the mint-glowing screen and the front armchairs. "
        "CENTRE: a small wooden stand with an open notebook under a little brass lamp. "
        "RIGHT: a snug alcove — deep sofa piled with cushions, low table with two steaming mugs, "
        "a shelf of film reels and trailing plants beside it, a paper lantern, a sleeping cat. "
        "A window at the back shows a soft blurred blue night city. "
        "Deep, layered, warm, healing. Nobody in frame."
    ),

    # ---------- 角色参考图（先出这张，之后所有含人的图都 --ref 它） ----------
    "char": (
        "CHARACTER REFERENCE. {char} stands relaxed, three-quarter view, full body, "
        "against a plain soft warm-grey background with gentle rim light. "
        "Clear, readable, well-lit — this image exists to lock the design. "
        "One figure only, centred."
    ),

    # ---------- 幕布上放的地图（点「看作品」后放映的内容） ----------
    "map": (
        "A hand-painted world map filling the whole frame, as if it is being PROJECTED onto "
        "a cinema screen — soft projector vignette darkening the corners, gentle light haze, "
        "faint horizontal scan of dust and grain over everything, slightly warm and faded. "
        "The map itself looks like aged paper: warm cream landmasses, muted teal oceans, "
        "soft hand-drawn coastlines, delicate contour hatching, no country borders drawn harshly. "
        "The map is CLEAN AND UNMARKED — no pins, no dots, no glowing points, no markers, "
        "no highlighted regions, no routes, no place names, no labels, no text of any kind. "
        "Standard equirectangular world map, correct familiar continent shapes and proportions, "
        "the whole world visible and evenly filling the screen. "
        "Beautiful, calm, analogue."
    ),

    # ---------- 全画幅地图（真正用来打点的那张） ----------
    "map-full": (
        "The camera is pushed all the way in on the cinema screen, so the PROJECTED MAP FILLS THE "
        "ENTIRE FRAME edge to edge — no room, no furniture, no screen border visible. "
        "It reads as aged paper lit by a projector: warm cream landmasses, muted teal oceans, "
        "soft hand-drawn coastlines, delicate contour hatching in the seas, gentle paper texture. "
        "Over it: a soft projector vignette darkening the corners, faint light haze, drifting dust "
        "motes, subtle grain — you can tell this is light thrown onto a surface, not a flat graphic. "
        "Standard equirectangular projection with correct, familiar continent shapes and proportions; "
        "the whole world evenly composed and centred, continents comfortably inside the frame. "
        "CLEAN AND UNMARKED — no pins, no dots, no glowing points, no markers, no highlighted "
        "countries, no borders, no routes, no place names, no labels, no text of any kind."
    ),

    # ---------- 项目海报（卡片用，2:3，绝不烧字） ----------
    # 文字全部由 HTML 叠加，所以海报只负责意象和气氛。
    "poster-didi-au": (
        "Bright late-afternoon photograph of a wide Melbourne street, low sun raking down the road. "
        "Tram tracks and overhead wires, Victorian brick facades on one side and glass towers behind, "
        "plane trees along the kerb. An orange sedan waits at the lights in the middle distance, "
        "indicator on. Long warm shadows, clear blue sky, crisp air. "
        "Palette: warm orange #FF4A00 against blue sky, grey asphalt and red brick. "
        "Ordinary, specific, unmistakably Australian. "
        "Composition: the street receding to the right, sunlit empty road across the LOWER LEFT."
    ),

    "poster-didi-mx": (
        "Bright daylight photograph of a wide busy avenue in Mexico City, seen at street level. "
        "Traffic, palm trees, low colonial buildings in warm pinks and ochres behind, "
        "the volcanoes faint on the horizon. Strong high sun, crisp shadows, clear blue sky. "
        "An orange car moves through the middle of the frame, motion slightly blurred. "
        "Palette dominated by warm orange #FF4A00 against blue sky and sun-bleached stucco. "
        "Energetic, everyday, unmistakably Mexico City. "
        "Composition: the avenue receding to the right, open sunlit road across the LOWER LEFT."
    ),

    "poster-99": (
        "Bright daylight advertising photography, clean and optimistic. A woman stands in a modern "
        "Brazilian city street, glass office towers and blue sky behind her, looking down at a phone "
        "held in both hands with a small easy smile. She wears a plain warm-yellow t-shirt. "
        "The phone case is the same yellow. Strong midday sun, crisp shadows, clear blue sky, "
        "saturated but natural colour. "
        "Palette dominated by bright taxi yellow #FFD400 against sky blue and glass grey. "
        "Commercial, friendly, everyday. NOT a celebrity, an ordinary person. "
        "Composition: the woman right of centre, open street and sky across the LOWER LEFT."
    ),

    "poster-actionway": (
        "A dark studio interior. From the LEFT edge, dozens of fine luminous filaments of different "
        "colours stream inward through the air \u2014 loose, uneven, tangled, each on its own path. "
        "They all pass through a single upright aperture standing in the middle distance: a tall, "
        "thin slot of pure white light, edge-on, almost architectural. "
        "On the RIGHT side of the aperture the same filaments continue, but now parallel, evenly "
        "spaced and perfectly ordered, receding into the dark. "
        "The only light in the frame is the filaments and the slot. Faint haze catches the glow. "
        "Palette strictly cool white #f2f6ff, pale amber #e8b06a, soft periwinkle #7c9cd8, near-black. "
        "No people, no furniture, no devices, no screens showing content. "
        "Composition: the aperture slightly left of centre, ordered filaments and empty black "
        "filling the RIGHT THIRD of the frame."
    ),

    "poster-roboneo": (
        "An enormous smooth abstract sculptural form floating in a pitch-black void, lit from within: "
        "soft liquid gradients of ice blue bleeding into pink and lilac, glossy and weightless, like "
        "a single brushstroke frozen in three dimensions. No hard edges, no visible light source, "
        "just the form glowing against absolute black. Faint haze catches the colour around it. "
        "Two or three people stand very small at the bottom of frame, silhouetted, looking up at it. "
        "Palette strictly ice blue #cfe4f5, lilac #c9b8ee, soft pink #e9b6dd, pure black. "
        "Serene, futuristic, quietly monumental. "
        "Composition: the form filling the upper right, black empty space across the LOWER LEFT."
    ),

    "poster-vmake": (
        "A warm, well-dressed creator studio at night. In sharp focus on the RIGHT, one woman sits "
        "on a stool facing her phone on a tripod, caught mid-sentence talking straight to camera, "
        "holding a small product up beside her face in a natural explaining gesture, genuinely "
        "animated and enjoying it. A ring light softly frames her. "
        "Behind her, thrown well out of focus, two more filming setups glow in the depth of the "
        "room, each different, suggesting a working studio rather than a production line. "
        "Warm honey light, shallow depth of field, relaxed and professional. "
        "Composition: the creator right of centre, soft dark studio floor across the LOWER LEFT."
    ),

    "poster-creative": (
        "A dark studio wall completely covered in glowing VERTICAL 9:16 PHONE SCREENS in a tight "
        "grid, every one of them showing a SHORT-FORM VIDEO FEED POST. Each screen has the same "
        "familiar furniture: a thin segmented progress bar across the top, a full-bleed video "
        "frame, a vertical column of small round action icons stacked down the right edge, and a "
        "two-line caption bar across the bottom. Every screen is a variant of the same ad: same "
        "product, different opening frame, different crop, different colour grade, different "
        "caption block. Hundreds of them. "
        "GENERIC UI ONLY: no brand marks, no recognisable logos, no readable words, "
        "the captions are illegible texture. "
        "On the far LEFT one larger screen sits alone showing the original master post, brighter, "
        "with fine light threads fanning out from it into the grid. "
        "A person stands small in front of the wall, back to camera, silhouetted. "
        "Cool screen-white and pale amber glow against near-black, faint haze. "
        "Composition: master at left, grid filling the frame, dark floor across the LOWER LEFT."
    ),

    "poster-ilands": (
        "Five gentle AI CHARACTERS sitting close around a small round wooden table playing cards, "
        "late at night in a quiet room. Each has a smooth featureless rounded head like a soft "
        "knitted hood with no face at all, each a different muted colour: oatmeal, sage, clay, "
        "dusty blue, warm grey. They lean toward each other, one gesturing mid-sentence, one "
        "holding cards close, one reaching for a small pile of coins. Mugs on the table. "
        "One low pendant lamp directly above pools warm honey light on the table and their hands, "
        "and the rest of the room falls away into soft brown darkness. "
        "Companionable and unhurried, like friends who have done this many nights. "
        "Composition: the group right of centre, quiet empty darkness across the LOWER LEFT."
    ),

    "poster-mvland": (
        "A tiny bedroom music studio shot dead-on and perfectly symmetrical, like a cutaway of a "
        "doll's house. Centre: a plump friendly HIPPOPOTAMUS seated square to camera at a small "
        "desk, oversized headphones on its ears, front feet resting on a little keyboard, "
        "facing the viewer with a calm deadpan expression. It wears a small mustard cardigan. "
        "Behind it a wall of neatly arranged, evenly spaced things: a mint synthesiser, a coral "
        "guitar on a hook, mustard record sleeves in a row, a powder-blue tape deck, small potted "
        "plants at matching heights, framed pictures aligned to a grid. "
        "Two identical lamps flank the desk in perfect mirror symmetry. "
        "Flat even light, pastel palette, no dramatic shadow, gently absurd and charming. "
        "Composition: absolutely centred and level, with calm empty wall in the LOWER LEFT."
    ),

    "poster-dramaland": (
        "A small sweaty rock club, deep in the set. Shot from inside the crowd, over silhouetted "
        "heads and raised fists. On a low stage a few feet away the singer is mid-scream into the "
        "mic, hair flying, guitarist lunging beside her, drummer hammering behind — loud, physical, "
        "unglamorous. Crimson and magenta wash cuts through haze and cigarette smoke; a hard white "
        "flash catches the sweat. Stickered amps, taped cables, a low ceiling. "
        "Composition: the band right-of-centre, the darker crowd filling the LOWER LEFT."
    ),

    # ---------- 沙发角（聊两句用，带人物） ----------
    "sofa": (
        "INTERIOR medium shot of the snug alcove in the screening room: {char} sits sideways on "
        "the soft sofa, one leg tucked up, holding a warm mug in both hands, "
        "turned slightly toward the viewer as if you just sat down opposite her. "
        "A paper lantern glows honey-amber above; a cat sleeps on the cushion beside her; "
        "a low table with a second steaming mug in the foreground. "
        "Warm, unhurried, off-the-clock. Leave clear negative space on the LEFT of frame."
    ),

    # ---------- 门厅（首屏，关键图定了之后再出） ----------
    "lobby": (
        "INTERIOR wide symmetrical shot of a tiny cinema lobby at night, camera straight on. "
        "CENTRE: a pair of closed padded double doors, a warm sliver of light spilling from under them — "
        "the clear focal point, dead centre, framed with space around it. "
        "LEFT: a small unattended ticket booth with a lamp on. "
        "RIGHT: an empty velvet rope stand and a blank backlit poster frame. "
        "Worn patterned carpet leading to the doors. Cool ambient, one warm accent. Nobody in frame."
    ),
}


def load_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY", "")


def img_part(path):
    return {"inline_data": {"mime_type": "image/jpeg",
                            "data": base64.b64encode(pathlib.Path(path).read_bytes()).decode()}}


def generate(name, out_name, ref=None, charref=None):
    shot = SHOTS[name]
    if name.startswith("poster-"):                       # 海报：只继承画法
        look = (CINEMA_LOOK if name in CINEMA_COVERS
                else SUBLIME_LOOK if name in SUBLIME_COVERS
                else WARM_LOOK if name in WARM_COVERS
                else BRIGHT_LOOK if name in BRIGHT_COVERS
                else TECH_LOOK if name in TECH_COVERS
                else COVER_LOOK)
        prompt = f"{look}{POSTER}\n\nCOVER: {shot}"
    elif "{char}" in shot:                               # 房间 + 人物
        prompt = f"{LOOK}{ROOM}\n\n{CHARACTER}\n\nSHOT: {shot.replace('{char}', 'the character')}"
    else:                                                # 房间空镜
        prompt = f"{LOOK}{ROOM}{EMPTY}\n\nSHOT: {shot}"
    parts = [{"text": prompt}]

    # 可以同时喂两张垫图：房间图定光线氛围，角色图定长相造型
    notes = []
    if ref:
        parts.insert(len(notes), img_part(ref)); notes.append(
            "IMAGE 1 is the reference for lighting, palette, rendering style, grade and set dressing — "
            "same room, same night, same lamps. Do NOT copy its composition.")
    if charref:
        parts.insert(len(notes), img_part(charref)); notes.append(
            f"IMAGE {len(notes) + 1} is the character reference. Reproduce this exact person — "
            "same face, same hairstyle with the braids and the teal streak, same outfit and jewellery. "
            "Re-pose and re-light her to fit the scene; do not redesign her.")
    if notes:
        parts[-1] = {"text": "\n".join(notes) + "\n\n" + prompt}

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {"imageConfig": {"aspectRatio": "16:9"}},
    }
    req = urllib.request.Request(
        API.format(MODEL, load_key()),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.load(r)

    for part in data["candidates"][0]["content"]["parts"]:
        blob = part.get("inlineData") or part.get("inline_data")
        if blob:
            OUT.mkdir(parents=True, exist_ok=True)
            path = OUT / f"{out_name}.jpg"
            path.write_bytes(base64.b64decode(blob["data"]))
            return path
    raise RuntimeError("没返回图片：" + json.dumps(data)[:300])


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--list":
        for k in SHOTS:
            print(" ", k)
        sys.exit()

    ref, charref, n, names = None, None, 1, []
    i = 0
    while i < len(args):
        if args[i] == "--ref":
            ref = args[i + 1]; i += 2
        elif args[i] == "--char":
            charref = args[i + 1]; i += 2
        elif args[i] == "--n":
            n = int(args[i + 1]); i += 2
        else:
            names.append(args[i]); i += 1

    for name in names:
        if name not in SHOTS:
            print(f"✗ 没有 {name}"); continue
        for k in range(n):
            out = name if n == 1 else f"{name}-{k + 1}"
            try:
                p = generate(name, out, ref, charref)
                print(f"✓ {out} → {p.relative_to(ROOT)} ({p.stat().st_size // 1024} KB)")
            except Exception as e:
                print(f"✗ {out}: {e}")
