"""收件口：本机 HTTP，给快捷指令 / Siri / 菜单栏小程序 / curl 投话用。

  POST /say        body 是一句话，返回念回去的那句
  GET  /status     进度
  POST /confirm/a  发
  POST /cancel/a   算了
  POST /revise/a   body 是修改意见

只听 127.0.0.1，外面进不来。手机上要用走 ntfy（见 notify.py）。
"""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def start(session, loop: asyncio.AbstractEventLoop, port: int = 8765) -> ThreadingHTTPServer:
    def run(fn, *a):
        """在事件循环线程里跑，因为 dispatcher 要 ensure_future。"""
        fut = asyncio.run_coroutine_threadsafe(_call(fn, *a), loop)
        return fut.result(timeout=30)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):            # 别刷终端
            pass

        def _body(self) -> str:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n).decode("utf-8", "replace") if n else ""
            # 快捷指令有时发 JSON {"text": "..."}
            if raw.startswith("{"):
                try:
                    return str(json.loads(raw).get("text", ""))
                except json.JSONDecodeError:
                    pass
            return raw

        def _reply(self, text: str, code: int = 200):
            data = text.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/status":
                return self._reply(run(session.disp.status))
            self._reply("not found", 404)

        def do_POST(self):
            parts = self.path.strip("/").split("/")
            if parts[0] == "say":
                return self._reply(run(session.handle, self._body()))
            if len(parts) == 2 and parts[0] in ("confirm", "cancel", "revise"):
                tid = parts[1]
                if parts[0] == "confirm":
                    return self._reply(run(session.disp.confirm, tid))
                if parts[0] == "cancel":
                    return self._reply(run(session.disp.cancel, tid))
                return self._reply(run(session.disp.revise, tid, self._body()))
            self._reply("not found", 404)

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def _call(fn, *a):
    return fn(*a)
