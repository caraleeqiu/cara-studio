"""入口：说一句、走开、回来点头。

  python -m voice_router                          # 打字模式，每行一句派活
  python -m voice_router --listen                 # 麦克风，回车开始 / 结束
  python -m voice_router --ntfy 你的topic          # 手机推送 + 手机上确认
  python -m voice_router --claude-bin /path/claude

派活之后的口令（打字或说都行）：
  进度            看所有活
  看 a            看 a 的草稿全文
  发 a            确认执行
  算了 a          作废
  改 a 语气软一点   改草稿
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import tempfile

from .dispatcher import Dispatcher, TaskState
from .notify import MacNotifier, NtfyNotifier
from .planner import Planner
from .workers import ClaudeCodeWorker, LocalWorker

READBACK_SECONDS = 3
_CMD = re.compile(r"^(进度|status|看|发|算了|改|取消)\s*([a-z]\d*)?\s*(.*)$", re.S)


def build(args):
    notifiers = [MacNotifier()]
    ntfy = NtfyNotifier(args.ntfy) if args.ntfy else None
    if ntfy:
        notifiers.append(ntfy)

    def on_change(st: TaskState):
        print(f"  [{st.task.id}] {st.status}" + (f"\n{indent(st.result)}" if st.status in ("done", "draft", "failed") else ""))

    disp = Dispatcher(
        workers={"claude_code": ClaudeCodeWorker(args.claude_bin, cwd=args.cwd),
                 "local": LocalWorker()},
        notifiers=notifiers, on_change=on_change)
    return disp, Planner(), notifiers[0], ntfy


def indent(s: str, n: int = 6) -> str:
    return "\n".join(" " * n + line for line in s.strip().splitlines()[:40])


async def handle(text: str, disp: Dispatcher, planner: Planner, mac: MacNotifier):
    m = _CMD.match(text.strip())
    if m:
        verb, tid, rest = m.group(1), m.group(2), m.group(3).strip()
        if verb in ("进度", "status"):
            print(disp.status()); return
        if not tid:
            drafts = disp.drafts()
            if len(drafts) == 1:
                tid = drafts[0].task.id          # 只有一份草稿时不用报 id
            else:
                print("哪一件？说 id。\n" + disp.status()); return
        if verb == "看":
            st = disp.states.get(tid); print(indent(st.result) if st else "没这件"); return
        if verb == "发":
            print(disp.confirm(tid)); return
        if verb in ("算了", "取消"):
            print(disp.cancel(tid)); return
        if verb == "改":
            print(disp.revise(tid, rest)); return

    tl = planner.plan(text)
    if not tl.tasks:
        print(tl.say); return
    print(f"  {tl.say}")
    mac.say(tl.say)
    # 念回来之后给几秒打断，识别错了派错活比等三秒贵得多。非交互（管道、--text）不等。
    if sys.stdin.isatty():
        print(f"  {READBACK_SECONDS} 秒内回车取消…", end="", flush=True)
        try:
            await asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline),
                                   READBACK_SECONDS)
            print(" 取消了"); return
        except asyncio.TimeoutError:
            print(" 开始")
    ids = disp.submit(tl)
    print("  派了：" + "、".join(ids))


async def main_async(args) -> int:
    disp, planner, mac, ntfy = build(args)
    loop = asyncio.get_event_loop()
    if ntfy:
        ntfy.listen(lambda verb, tid: print("\n  [手机] " + (disp.confirm(tid) if verb == "confirm" else disp.cancel(tid))),
                    loop)

    if args.text:
        await handle(args.text, disp, planner, mac)
        await disp.wait_all()
        return 0

    get = None
    if args.listen:
        from .listen import record
        from .stt import STT
        stt = STT(args.stt_model, "zh")
        tmp = os.path.join(tempfile.gettempdir(), "voice_router_last.wav")

        def get():
            record(tmp)
            t = stt.transcribe(tmp)
            print(f"听到：{t}")
            return t
    else:
        def get():
            return input("> ")

    print(__doc__)
    try:
        while True:
            text = await loop.run_in_executor(None, get)
            if text is None:
                break
            if text.strip():
                await handle(text, disp, planner, mac)
    except (KeyboardInterrupt, EOFError):
        print()
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="voice_router", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--text", "-t", help="只派这一句，跑完退出")
    p.add_argument("--listen", action="store_true", help="用麦克风")
    p.add_argument("--ntfy", help="ntfy topic，给了就推手机并接受手机确认")
    p.add_argument("--claude-bin", default="claude")
    p.add_argument("--cwd", default=None, help="claude -p 的工作目录")
    p.add_argument("--stt-model", default="small")
    args = p.parse_args(argv)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
