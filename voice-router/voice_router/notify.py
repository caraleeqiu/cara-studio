"""通知：Mac 弹窗 + 手机推送。

手机推送走 ntfy。通知上带「发 / 算了」按钮，按钮不直接打 Mac
（Mac 不在公网），而是往 ntfy 的另一个 topic 发一条回执，Mac 订阅那个 topic。
这样走开之后在手机上就能确认。
"""

from __future__ import annotations

import asyncio
import json
import platform
import subprocess
import sys
import threading
import urllib.request


class MacNotifier:
    def __init__(self):
        self.mac = platform.system() == "Darwin"

    def push(self, title: str, body: str):
        if not self.mac:
            print(f"  [通知] {title}：{body}")
            return
        script = f'display notification "{_esc(body)}" with title "{_esc(title)}"'
        subprocess.run(["osascript", "-e", script], check=False)

    def say(self, text: str):
        if self.mac:
            subprocess.Popen(["say", text])
        else:
            print(f"  [念] {text}")


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')[:900]


class NtfyNotifier:
    """一个 topic 发通知，<topic>-reply 收手机上按的按钮。"""

    def __init__(self, topic: str, server: str = "https://ntfy.sh"):
        self.server = server.rstrip("/")
        self.topic = topic
        self.reply_topic = topic + "-in"      # 按钮回执和手机上派的活都进这里

    def push(self, title: str, body: str, task_id: str | None = None, confirmable: bool = False):
        headers = {"Title": title.encode("utf-8").decode("latin-1", "replace"),
                   "Content-Type": "text/plain; charset=utf-8"}
        if confirmable and task_id:
            reply = f"{self.server}/{self.reply_topic}"
            headers["Actions"] = (
                f"http, Send, {reply}, method=POST, body=confirm:{task_id}, clear=true; "
                f"http, Cancel, {reply}, method=POST, body=cancel:{task_id}, clear=true")
        req = urllib.request.Request(f"{self.server}/{self.topic}", data=body.encode("utf-8"),
                                     headers=headers, method="POST")
        try:
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as e:
            print(f"[ntfy] 推送失败：{e}", file=sys.stderr)

    def listen(self, on_message, loop: asyncio.AbstractEventLoop):
        """后台线程订阅 -in topic，每条消息原样丢回事件循环。
        消息可能是按钮回执 confirm:a / cancel:a，也可能是手机上说的一整句话。"""
        def run():
            url = f"{self.server}/{self.reply_topic}/json"
            while True:
                try:
                    with urllib.request.urlopen(url, timeout=None) as resp:
                        for line in resp:
                            try:
                                j = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if j.get("event") != "message":
                                continue
                            msg = str(j.get("message", "")).strip()
                            if msg:
                                loop.call_soon_threadsafe(on_message, msg)
                except Exception as e:
                    print(f"[ntfy] 订阅断了，5 秒后重连：{e}", file=sys.stderr)
                    threading.Event().wait(5)
        threading.Thread(target=run, daemon=True).start()


def parse_reply(message: str) -> tuple[str, str] | None:
    verb, _, tid = message.partition(":")
    return (verb, tid) if verb in ("confirm", "cancel") and tid else None
