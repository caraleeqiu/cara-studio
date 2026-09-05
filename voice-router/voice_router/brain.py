"""把一句话变成 Command。

有 ANTHROPIC_API_KEY 就走 Claude 的结构化输出；没有就退到关键词兜底，
并且诚实地说一声，不装作听懂了。
"""

from __future__ import annotations

import json
import os
import sys

from .routes import Routes
from .schema import COMMAND_SCHEMA, Arg, Command

MODEL = "claude-opus-5"

SYSTEM = """你是一个语音指令路由器。用户说的话来自语音识别，可能有错字、同音字、口语。
你的工作只有一件：判断它属于哪个意图，抽出参数，输出 JSON。

规则：
- intent 必须是下面列表里的名字之一。不像命令、或者听不清的，一律归到 chat。
- 参数只填用户明确说了的，没说的不要编。
- say 是回给用户的一句话，十个字以内，口语，像人说的。
- confidence 是你有多确定。识别文本很怪、或者两种意图都像，就给低。

可用意图：
{intents}
"""


class Brain:
    def __init__(self, routes: Routes, model: str = MODEL, effort: str = "low"):
        self.routes = routes
        self.model = model
        self.effort = effort
        self._client = None
        self.live = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        if not self.live:
            print("[brain] 没有 ANTHROPIC_API_KEY，走关键词兜底。能演，不能用。", file=sys.stderr)

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def route(self, text: str) -> Command:
        text = text.strip()
        if not text:
            return Command(intent="chat", args=[Arg(name="text", value="")], say="没听到", confidence=0.0)
        if not self.live:
            return self.routes.keyword_route(text)
        try:
            cmd = self._ask(text)
        except Exception as e:                       # 网络、限流、解析失败都不该让主循环死
            print(f"[brain] 模型调用失败，退到关键词：{e}", file=sys.stderr)
            return self.routes.keyword_route(text)
        return self.routes.validate(cmd, text)

    def _ask(self, text: str) -> Command:
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=512,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",                     # 被安全分类器拒了就服务端换模型重跑
            system=SYSTEM.format(intents=self.routes.describe()),
            messages=[{"role": "user", "content": text}],
            output_config={
                "effort": self.effort,               # 分类任务，低 effort 够用，快
                "format": {"type": "json_schema", "schema": COMMAND_SCHEMA},
            },
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"模型拒答：{resp.stop_details}")
        raw = next(b.text for b in resp.content if b.type == "text")
        return Command.model_validate(json.loads(raw))
