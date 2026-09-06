"""App 表：点名了认别名，没点名按能力查默认。给拆任务用。"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


class Apps:
    def __init__(self, path: str | Path = HERE / "apps.json"):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.defaults: dict[str, str] = raw.get("defaults", {})
        self.apps: dict[str, dict] = raw.get("apps", {})
        self._alias = {}
        for name, a in self.apps.items():
            self._alias[name.lower()] = name
            for al in a.get("aliases", []):
                self._alias[al.lower()] = name

    def resolve(self, name: str) -> str | None:
        """「微信」「wechat」「vx」都回 微信；不认识回 None。"""
        return self._alias.get(name.strip().lower())

    def default_for(self, capability: str) -> str | None:
        return self.defaults.get(capability)

    def mentioned(self, text: str) -> list[str]:
        """一句话里点名了哪些 App，长别名优先，避免「claude」吃掉「claude code」。"""
        low = text.lower()
        hits, taken = [], []
        for al in sorted(self._alias, key=len, reverse=True):
            i = low.find(al)
            if i < 0 or any(s <= i < e for s, e in taken):
                continue
            name = self._alias[al]
            if name not in hits:
                hits.append(name)
            taken.append((i, i + len(al)))
        return hits

    def describe(self) -> str:
        """给模型看的表：能力 → 默认，以及每个 App 有哪几级。"""
        lines = ["没点名时按能力选默认 App：" +
                 "，".join(f"{cap}→{app}" for cap, app in self.defaults.items())]
        for name, a in self.apps.items():
            chans = [k for k in ("mcp", "cli", "applescript", "web") if a.get(k)]
            if a.get("gui_only"):
                chans.append("只能点界面")
            lines.append(f"- {name}（{a.get('capability')}）通道：{'、'.join(chans) or '未知'}；"
                         f"别名：{'、'.join(a.get('aliases', [])) or '无'}")
        return "\n".join(lines)
