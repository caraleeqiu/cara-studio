"""收件口和 Session：快捷指令 / Siri / 手机投进来的话能不能走通。"""

import asyncio
import sys
import threading
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FAKE = str(ROOT / "tests" / "fake_claude.py")

from voice_router import inbox                       # noqa: E402
from voice_router.app import Session                 # noqa: E402
from voice_router.dispatcher import Dispatcher       # noqa: E402
from voice_router.planner import Planner             # noqa: E402
from voice_router.workers import ClaudeCodeWorker, LocalWorker   # noqa: E402


def make_session():
    d = Dispatcher(workers={"claude_code": ClaudeCodeWorker(FAKE), "local": LocalWorker()})
    with mock.patch.dict("os.environ", {}, clear=True):
        return Session(d, Planner())


class TestSession(unittest.TestCase):
    def test_dispatch_and_commands(self):
        s = make_session()
        async def go():
            out = s.handle("查一下 X 同时回复老张")
            self.assertIn("派了 a、b", out)
            await s.disp.wait_all()
            self.assertEqual(s.disp.states["b"].status, "draft")
            self.assertIn("draft", s.handle("进度"))
            self.assertIn("做完了", s.handle("看"))          # 只有一份草稿，不用报 id
            self.assertIn("改着", s.handle("改 b 短一点"))
            await s.disp.wait_all()
            self.assertIn("发了", s.handle("confirm:b"))     # 手机按钮回执
            await s.disp.wait_all()
            self.assertEqual(s.disp.states["b"].status, "done")
        asyncio.new_event_loop().run_until_complete(go())

    def test_empty(self):
        self.assertEqual(make_session().handle("  "), "没听到")


class TestInbox(unittest.TestCase):
    def test_http_roundtrip(self):
        s = make_session()
        loop = asyncio.new_event_loop()
        srv = inbox.start(s, loop, port=0)
        port = srv.server_address[1]
        base = f"http://127.0.0.1:{port}"

        def post(path, body=""):
            req = urllib.request.Request(base + path, data=body.encode("utf-8"), method="POST")
            return urllib.request.urlopen(req, timeout=5).read().decode("utf-8")

        async def go():
            r = await loop.run_in_executor(None, post, "/say", "打开微信")
            self.assertIn("派了 a", r)
            await s.disp.wait_all()
            r = await loop.run_in_executor(None, post, "/say", '{"text": "回复老张说好"}')   # 快捷指令发 JSON
            self.assertIn("派了 b", r)
            await s.disp.wait_all()
            st = await loop.run_in_executor(None, lambda: urllib.request.urlopen(base + "/status", timeout=5).read().decode())
            self.assertIn("draft", st)
            r = await loop.run_in_executor(None, post, "/confirm/b")
            self.assertIn("发了", r)
            await s.disp.wait_all()
            self.assertEqual(s.disp.states["b"].status, "done")
        try:
            loop.run_until_complete(go())
        finally:
            srv.shutdown()
            loop.close()


if __name__ == "__main__":
    unittest.main()
