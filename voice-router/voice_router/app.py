"""Session：调度器外面那一层，谁来的话都走这里。

REPL 打字、麦克风、Siri 快捷指令、手机 ntfy、菜单栏小程序，最后都调 handle(text)。
返回一句话给来源念回去（Siri 会读出来）。
"""

from __future__ import annotations

import re
import sys

from .dispatcher import Dispatcher
from .notify import parse_reply
from .planner import Planner

_CMD = re.compile(r"^(进度|status|看|发|算了|改|取消)\s*([a-z]\d*)?\s*(.*)$", re.S)


class Session:
    def __init__(self, dispatcher: Dispatcher, planner: Planner, say=None):
        self.disp = dispatcher
        self.planner = planner
        self.say = say or (lambda s: None)     # 念出来的钩子，Mac 上是 `say`

    def handle(self, text: str) -> str:
        """一句话进来，一句话出去。派活时不等三秒，来源自己决定要不要给打断窗口。"""
        text = text.strip()
        if not text:
            return "没听到"
        r = _reply(text)                          # 手机按钮回执 confirm:a / cancel:a
        if r:
            return self._command(*r)
        m = _CMD.match(text)
        if m:
            return self._command(*m.groups())
        tl = self.planner.plan(text)
        if not tl.tasks:
            return tl.say
        ids = self.disp.submit(tl)
        self.say(tl.say)
        return f"{tl.say}。派了 {'、'.join(ids)}"

    def plan_only(self, text: str):
        """给想先念回来再派的来源用：先拿 TaskList，确认后 submit。"""
        return self.planner.plan(text)

    def _command(self, verb, tid, rest) -> str:
        if verb in ("进度", "status"):
            return self.disp.status()
        if not tid:
            drafts = self.disp.drafts()
            if len(drafts) != 1:
                return "哪一件？说 id。\n" + self.disp.status()
            tid = drafts[0].task.id
        if verb == "看":
            st = self.disp.states.get(tid)
            return st.result if st else "没这件"
        if verb == "发":
            return self.disp.confirm(tid)
        if verb in ("算了", "取消"):
            return self.disp.cancel(tid)
        if verb == "改":
            return self.disp.revise(tid, rest.strip()) if rest.strip() else "改什么？"
        return "？"


def _reply(text: str):
    r = parse_reply(text)
    if not r:
        return None
    verb, tid = r
    return ("发" if verb == "confirm" else "算了", tid, "")
