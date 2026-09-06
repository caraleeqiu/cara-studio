"""调度器离线测试：假 claude、不联网、不碰 Mac。"""

import asyncio
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FAKE = str(ROOT / "tests" / "fake_claude.py")

from voice_router.dispatcher import Dispatcher                          # noqa: E402
from voice_router.notify import NtfyNotifier, parse_reply               # noqa: E402
from voice_router.planner import Planner, naive_plan                    # noqa: E402
from voice_router.schema import TASKLIST_SCHEMA, Task, TaskList         # noqa: E402
from voice_router.workers import ClaudeCodeWorker, LocalWorker          # noqa: E402


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def make(notifiers=None):
    return Dispatcher(workers={"claude_code": ClaudeCodeWorker(FAKE), "local": LocalWorker()},
                      notifiers=notifiers or [])


class TestPlannerFallback(unittest.TestCase):
    def test_splits_on_connectives(self):
        tl = naive_plan("打开 Claude Code 查一下 X，同时打开 Gmail 回复一下老张")
        self.assertEqual(len(tl.tasks), 2)
        self.assertEqual([t.worker for t in tl.tasks], ["claude_code", "claude_code"])
        self.assertFalse(tl.tasks[0].needs_confirm)
        self.assertTrue(tl.tasks[1].needs_confirm)

    def test_plain_open_is_local(self):
        tl = naive_plan("打开微信")
        self.assertEqual(tl.tasks[0].worker, "local")
        self.assertEqual(tl.tasks[0].action, "switch_app")
        self.assertEqual(tl.tasks[0].instruction, "微信")

    def test_offline_planner_uses_fallback(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            p = Planner()
        self.assertFalse(p.live)
        self.assertEqual(len(p.plan("查 A 然后查 B").tasks), 2)

    def test_live_planner_request_shape_and_id_dedupe(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x"}):
            p = Planner()
        fake = mock.Mock(stop_reason="end_turn")
        fake.content = [mock.Mock(type="text", text=json.dumps({"tasks": [
            {"id": "a", "worker": "claude_code", "action": "run", "instruction": "查 X", "capability": "other", "app": "", "needs_confirm": False, "notify": True},
            {"id": "a", "worker": "claude_code", "action": "run", "instruction": "回 Y", "capability": "email", "app": "gmail", "needs_confirm": True, "notify": True},
        ], "say": "两件事"}))]
        with mock.patch.object(Planner, "client", new_callable=mock.PropertyMock) as c:
            c.return_value.beta.messages.create.return_value = fake
            tl = p.plan("查 X 同时回 Y")
            kw = c.return_value.beta.messages.create.call_args.kwargs
        self.assertEqual([t.id for t in tl.tasks], ["a", "b"])
        self.assertEqual(tl.tasks[1].app, "Gmail")           # 模型写 gmail，统一成标准名
        self.assertEqual(kw["fallbacks"], "default")
        self.assertEqual(kw["output_config"]["format"]["schema"], TASKLIST_SCHEMA)


class TestAppChoice(unittest.TestCase):
    def test_named_app_wins(self):
        t = naive_plan("用 Mail 回复老张").tasks[0]
        self.assertEqual(t.app, "Mail"); self.assertEqual(t.capability, "email")

    def test_alias(self):
        from voice_router.apps import Apps
        a = Apps()
        self.assertEqual(a.resolve("vx"), "微信")
        self.assertEqual(a.mentioned("打开 claude code 查一下"), ["Claude Code"])

    def test_default_by_capability(self):
        t = naive_plan("回复老张的邮件说周五可以").tasks[0]
        self.assertEqual(t.app, "Gmail")                     # 没点名，email 的默认
        self.assertEqual(naive_plan("查一下天气").tasks[0].app, "")

    def test_switch_app_uses_canonical_name(self):
        self.assertEqual(naive_plan("打开 wechat").tasks[0].instruction, "微信")


class TestDispatcher(unittest.TestCase):
    def test_tasks_run_in_parallel(self):
        d = make()
        tl = TaskList(say="", tasks=[
            Task(id="a", worker="claude_code", action="run", instruction="SLEEP=1 查 A", needs_confirm=False, notify=False),
            Task(id="b", worker="claude_code", action="run", instruction="SLEEP=1 查 B", needs_confirm=False, notify=False),
        ])
        async def go():
            t0 = time.monotonic()
            d.submit(tl)
            await d.wait_all()
            return time.monotonic() - t0
        elapsed = run(go())
        self.assertLess(elapsed, 1.9)                      # 串行要 2 秒以上
        self.assertEqual({s.status for s in d.states.values()}, {"done"})

    def test_draft_revise_confirm_loop(self):
        pushed = []
        n = mock.Mock(); n.topic = "t"; n.push = lambda title, body, task_id=None, confirmable=False: pushed.append((title, confirmable))
        d = make([n])
        tl = TaskList(say="", tasks=[Task(id="a", worker="claude_code", action="run",
                                          instruction="回复老张", needs_confirm=True, notify=True)])
        async def go():
            d.submit(tl); await d.wait_all()
            st = d.states["a"]
            self.assertEqual(st.status, "draft")
            self.assertIn("做完了", st.result)
            sid = st.session_id
            self.assertTrue(sid)

            d.revise("a", "语气软一点"); await d.wait_all()
            self.assertEqual(st.status, "draft")
            self.assertIn("新版本", st.result)
            self.assertEqual(st.session_id, sid)          # 同一个会话续着改
            self.assertEqual(len(st.history), 1)

            d.confirm("a"); await d.wait_all()
            self.assertEqual(st.status, "done")
            self.assertIn("已发送", st.result)
        run(go())
        self.assertEqual([c for _, c in pushed], [True, True, False])   # 草稿、改好、发了

    def test_confirm_only_in_draft(self):
        d = make()
        tl = TaskList(say="", tasks=[Task(id="a", worker="claude_code", action="run",
                                          instruction="查", needs_confirm=False, notify=False)])
        run(asyncio.wait_for(self._submit_and_wait(d, tl), 5))
        self.assertIn("不在等确认", d.confirm("a"))
        self.assertIn("已经结束", d.cancel("a"))

    async def _submit_and_wait(self, d, tl):
        d.submit(tl); await d.wait_all()

    def test_failure_is_reported_not_raised(self):
        d = make()
        tl = TaskList(say="", tasks=[Task(id="a", worker="claude_code", action="run",
                                          instruction="FAIL 查", needs_confirm=False, notify=False)])
        run(self._submit_and_wait(d, tl))
        self.assertEqual(d.states["a"].status, "failed")
        self.assertIn("炸", d.states["a"].result)

    def test_missing_claude_binary(self):
        d = Dispatcher(workers={"claude_code": ClaudeCodeWorker("/nonexistent/claude")})
        tl = TaskList(say="", tasks=[Task(id="a", worker="claude_code", action="run",
                                          instruction="查", needs_confirm=False, notify=False)])
        run(self._submit_and_wait(d, tl))
        self.assertEqual(d.states["a"].status, "failed")

    def test_duplicate_ids_across_submissions(self):
        d = make()
        mk = lambda: TaskList(say="", tasks=[Task(id="a", worker="local", action="switch_app",
                                                   instruction="微信", needs_confirm=False, notify=False)])
        async def go():
            d.submit(mk()); d.submit(mk()); await d.wait_all()
        run(go())
        self.assertEqual(sorted(d.states), ["a", "b"])

    def test_local_worker_off_mac_only_pretends(self):
        w = LocalWorker()
        if w.mac:
            self.skipTest("在 Mac 上会真切 App")
        r = run(w.run(Task(id="a", worker="local", action="dictate", instruction="你好",
                           needs_confirm=False, notify=False)))
        self.assertTrue(r.ok); self.assertIn("你好", r.text)


class TestNtfy(unittest.TestCase):
    def test_push_carries_action_buttons(self):
        n = NtfyNotifier("demo-topic")
        with mock.patch("urllib.request.urlopen") as u:
            n.push("a 等你确认", "正文", task_id="a", confirmable=True)
            req = u.call_args.args[0]
        self.assertEqual(req.full_url, "https://ntfy.sh/demo-topic")
        actions = req.get_header("Actions")
        self.assertIn("body=confirm:a", actions)
        self.assertIn("body=cancel:a", actions)
        self.assertIn("demo-topic-in", actions)

    def test_parse_reply(self):
        self.assertEqual(parse_reply("confirm:a"), ("confirm", "a"))
        self.assertIsNone(parse_reply("hello"))


if __name__ == "__main__":
    unittest.main()
