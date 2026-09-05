"""拆任务：一句话 → TaskList。

有 key 走 Claude 结构化输出；没 key 按「同时 / 然后 / 另外」切句，
「打开 X」归 local，其他都丢给 claude_code。兜底能演不能用。
"""

from __future__ import annotations

import json
import os
import re
import sys

from .schema import TASKLIST_SCHEMA, Task, TaskList

MODEL = "claude-opus-5"

SYSTEM = """你是一个派活助理。用户说一句话，你把它拆成几件独立的事，输出 JSON。
用户的话来自语音识别，会有错字、同音字、没断句。按意思理解，不按字面。

worker 只有两种：
- local：秒回的本地动作。action 取 switch_app（instruction 填 App 名）、open_url（填网址）、dictate（填要打的字）。
- claude_code：需要查、写、看、处理邮件日历文件的活。action 固定填 run。
  instruction 用第二人称交代，说清楚要什么结果。「查一下 X」要写成「查一下 X，给我三行结论」。

规则：
- 「同时」「另外」「然后」「还有」分开的是不同的事，各一个 task。
- 「打开 Claude Code 查 X」不是两件事，是一件 claude_code 的事。程序不用打开窗口。
- needs_confirm：发邮件、发消息、删东西、付钱、改别人能看到的东西，一律 true。查、读、写草稿 false。
- notify：用户说了「推我」「好了告诉我」，或者这件事要跑超过十秒，就 true。
- say 是念回给用户确认的一句话，格式「N 件事：A，B」，二十字以内。
- 听不懂就一个 claude_code 的 task，instruction 写「用户说：<原话>，猜一下他要什么并去做」，say 写「没太听清，我试试」。
"""


class Planner:
    def __init__(self, model: str = MODEL, effort: str = "low"):
        self.model = model
        self.effort = effort
        self._client = None
        self.live = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        if not self.live:
            print("[planner] 没有 ANTHROPIC_API_KEY，按连接词切句。能演，不能用。", file=sys.stderr)

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def plan(self, text: str) -> TaskList:
        text = text.strip()
        if not text:
            return TaskList(tasks=[], say="没听到")
        if not self.live:
            return naive_plan(text)
        try:
            return self._ask(text)
        except Exception as e:
            print(f"[planner] 模型调用失败，退到切句：{e}", file=sys.stderr)
            return naive_plan(text)

    def _ask(self, text: str) -> TaskList:
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=1024,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM,
            messages=[{"role": "user", "content": text}],
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": TASKLIST_SCHEMA},
            },
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"模型拒答：{resp.stop_details}")
        raw = next(b.text for b in resp.content if b.type == "text")
        tl = TaskList.model_validate(json.loads(raw))
        # id 去重，模型偶尔会都填 a
        seen = set()
        for i, t in enumerate(tl.tasks):
            if t.id in seen or not t.id:
                t.id = chr(ord("a") + i)
            seen.add(t.id)
        return tl


_SPLIT = re.compile(r"[，,。；;]?\s*(?:同时|另外|然后|还有|再)\s*")
_OPEN = re.compile(r"^(?:打开|切到|切换到|开)\s*(.+?)$")
_CONFIRM_WORDS = ("回复", "回他", "回她", "发给", "发邮件", "发消息", "删", "付", "转账")


def naive_plan(text: str) -> TaskList:
    parts = [p.strip(" ，,。") for p in _SPLIT.split(text) if p.strip(" ，,。")]
    tasks = []
    for i, p in enumerate(parts):
        tid = chr(ord("a") + i)
        m = _OPEN.match(p)
        if m and len(m.group(1)) <= 8 and not re.search(r"查|帮|把|找|回|发|删|写|看|读|做", m.group(1)):
            tasks.append(Task(id=tid, worker="local", action="switch_app", instruction=m.group(1),
                              needs_confirm=False, notify=False))
        else:
            # 「打开 Claude Code 查 X」里的「打开 Claude Code」是人的习惯，程序不用开窗口
            p = re.sub(r"^(?:打开|用|切到)\s*[A-Za-z][A-Za-z0-9 ]*?[A-Za-z0-9]\s*(?=[\u4e00-\u9fff])", "", p) or p
            tasks.append(Task(id=tid, worker="claude_code", action="run", instruction=p,
                              needs_confirm=any(w in p for w in _CONFIRM_WORDS), notify=True))
    say = f"{len(tasks)} 件事：" + "，".join(t.instruction[:8] for t in tasks) if tasks else "没听懂"
    return TaskList(tasks=tasks, say=say)
