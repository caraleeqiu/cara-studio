"""路由表：从 routes.json 读意图定义，生成给模型的说明，
以及没有模型时的关键词兜底。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .schema import Arg, Command

FALLBACK_INTENT = "chat"


@dataclass
class Intent:
    name: str
    desc: str
    args: dict[str, str] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    sink: str = "console"


@dataclass
class Routes:
    language: str
    intents: list[Intent]
    sinks: dict[str, dict]

    @classmethod
    def load(cls, path: str | Path) -> "Routes":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        intents = [Intent(**i) for i in raw["intents"]]
        names = [i.name for i in intents]
        if FALLBACK_INTENT not in names:
            raise ValueError(f"routes.json 必须有一个叫 {FALLBACK_INTENT} 的意图当兜底")
        if len(set(names)) != len(names):
            raise ValueError("意图名重复")
        return cls(language=raw.get("language", "zh"), intents=intents, sinks=raw.get("sinks", {}))

    def get(self, name: str) -> Intent | None:
        return next((i for i in self.intents if i.name == name), None)

    def sink_for(self, intent_name: str) -> str:
        i = self.get(intent_name)
        return i.sink if i else "console"

    # ---- 给模型看的说明。表改了这里自动跟着变，不用改 prompt。
    def describe(self) -> str:
        lines = []
        for i in self.intents:
            args = ", ".join(f"{k}: {v}" for k, v in i.args.items()) or "无"
            ex = " / ".join(i.examples) or "无"
            lines.append(f"- {i.name}：{i.desc}\n  参数：{args}\n  例子：{ex}")
        return "\n".join(lines)

    # ---- 没模型时的兜底。只做关键词匹配，能演不能用。
    def keyword_route(self, text: str) -> Command:
        q = text.lower()
        for i in self.intents:
            if any(k.lower() in q for k in i.keywords):
                return Command(intent=i.name, args=_guess_args(i.name, q, text),
                               say=f"{i.name}（关键词匹配）", confidence=0.3)
        return Command(intent=FALLBACK_INTENT, args=[Arg(name="text", value=text)],
                       say="没听懂", confidence=0.1)

    # ---- 模型回来的东西先过一遍表，意图不认识就打回兜底。
    def validate(self, cmd: Command, original: str) -> Command:
        if self.get(cmd.intent) is None:
            return Command(intent=FALLBACK_INTENT, args=[Arg(name="text", value=original)],
                           say=cmd.say or "没听懂", confidence=min(cmd.confidence, 0.2))
        return cmd


def _guess_args(intent: str, q: str, text: str) -> list[Arg]:
    """兜底模式下能猜就猜一两个参数，别太努力。"""
    if intent == "light":
        off = any(w in q for w in ("关", "off", "灭"))
        return [Arg(name="state", value="off" if off else "on")]
    if intent == "music":
        for word, action in (("暂停", "pause"), ("pause", "pause"), ("下一", "next"),
                             ("next", "next"), ("上一", "prev"), ("小", "volume"), ("大", "volume")):
            if word in q:
                return [Arg(name="action", value=action)]
        return [Arg(name="action", value="play")]
    if intent == "chat":
        return [Arg(name="text", value=text)]
    return []
