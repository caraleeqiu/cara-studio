"""调度器：任务的状态机 + 并行跑 + 通知。

状态：queued → running → done | failed
                       └→ draft → (revising → draft)* → done | cancelled
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .schema import Task, TaskList
from .workers import Result

STATUS_ICON = {"queued": "·", "running": "…", "draft": "?", "revising": "…",
               "done": "✓", "failed": "✗", "cancelled": "−"}


@dataclass
class TaskState:
    task: Task
    status: str = "queued"
    result: str = ""
    session_id: str | None = None
    history: list[str] = field(default_factory=list)


class Dispatcher:
    def __init__(self, workers: dict, notifiers: list | None = None, on_change=None):
        self.workers = workers
        self.notifiers = notifiers or []
        self.on_change = on_change or (lambda st: None)
        self.states: dict[str, TaskState] = {}
        self._tasks: set[asyncio.Task] = set()

    # ---- 派活
    def submit(self, tl: TaskList) -> list[str]:
        ids = []
        for t in tl.tasks:
            tid = self._unique(t.id)
            t.id = tid
            st = TaskState(task=t)
            self.states[tid] = st
            self._spawn(self._run(st))
            ids.append(tid)
        return ids

    def _unique(self, tid: str) -> str:
        """id 撞了就往后排字母：第二次派活的 a 变成 b，念起来顺口。"""
        if tid not in self.states:
            return tid
        for c in "abcdefghijklmnopqrstuvwxyz":
            if c not in self.states:
                return c
        n = 2
        while f"{tid}{n}" in self.states:
            n += 1
        return f"{tid}{n}"

    def _spawn(self, coro):
        t = asyncio.ensure_future(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def _run(self, st: TaskState):
        self._set(st, "running")
        worker = self.workers.get(st.task.worker)
        if worker is None:
            return self._finish(st, Result(text=f"没有 {st.task.worker} 这种 worker", ok=False))
        res = await worker.run(st.task)
        st.session_id = res.session_id or st.session_id
        if not res.ok:
            return self._finish(st, res)
        if st.task.needs_confirm:
            st.result = res.text
            self._set(st, "draft")
            self._notify(st, "等你确认", confirmable=True)
        else:
            self._finish(st, res)

    def _finish(self, st: TaskState, res: Result):
        st.result = res.text
        self._set(st, "done" if res.ok else "failed")
        if st.task.notify or not res.ok:
            self._notify(st, "好了" if res.ok else "失败了")

    # ---- 确认循环
    def confirm(self, tid: str) -> str:
        st = self.states.get(tid)
        if not st or st.status != "draft":
            return f"{tid} 现在不在等确认"
        self._spawn(self._confirm(st))
        return f"{tid} 发了"

    async def _confirm(self, st: TaskState):
        self._set(st, "running")
        worker = self.workers[st.task.worker]
        res = await worker.confirm(st.session_id) if st.session_id else Result(text="没有会话可续", ok=False)
        st.task.notify = True
        self._finish(st, res)

    def revise(self, tid: str, text: str) -> str:
        st = self.states.get(tid)
        if not st or st.status != "draft":
            return f"{tid} 现在不在等确认"
        self._spawn(self._revise(st, text))
        return f"{tid} 改着"

    async def _revise(self, st: TaskState, text: str):
        st.history.append(st.result)
        self._set(st, "revising")
        worker = self.workers[st.task.worker]
        res = await worker.revise(st.session_id, text) if st.session_id else Result(text="没有会话可续", ok=False)
        if not res.ok:
            return self._finish(st, res)
        st.result = res.text
        self._set(st, "draft")
        self._notify(st, "改好了，等你确认", confirmable=True)

    def cancel(self, tid: str) -> str:
        st = self.states.get(tid)
        if not st or st.status in ("done", "failed", "cancelled"):
            return f"{tid} 已经结束了"
        self._set(st, "cancelled")
        return f"{tid} 算了"

    # ---- 状态
    def _set(self, st: TaskState, status: str):
        st.status = status
        self.on_change(st)

    def _notify(self, st: TaskState, title: str, confirmable: bool = False):
        head = f"{st.task.id} {title}"
        for n in self.notifiers:
            try:
                n.push(head, st.result[:1500], task_id=st.task.id, confirmable=confirmable) \
                    if hasattr(n, "topic") else n.push(head, st.result[:200])
            except Exception as e:
                print(f"[notify] {e}")

    def status(self) -> str:
        if not self.states:
            return "没有活"
        lines = []
        for st in self.states.values():
            icon = STATUS_ICON.get(st.status, "?")
            lines.append(f"{icon} {st.task.id}  {st.status:<9} {st.task.instruction[:30]}")
        return "\n".join(lines)

    def drafts(self) -> list[TaskState]:
        return [s for s in self.states.values() if s.status == "draft"]

    async def wait_all(self):
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
