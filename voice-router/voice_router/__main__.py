"""入口：说一句、走开、回来点头。

  python -m voice_router --serve                  # 常驻后台：本机收件口 + 手机 ntfy。入口随便接
  python -m voice_router                          # 打字模式，每行一句
  python -m voice_router --listen                 # 麦克风，回车开始 / 结束
  python -m voice_router --text "…"               # 只派这一句
  python -m voice_router --ntfy 你的topic          # 手机推送、手机上确认、手机上派活

派活之后的口令（打字、说、或者 POST 到 127.0.0.1:8765/say 都行）：
  进度 / 看 a / 发 a / 算了 a / 改 a 语气软一点

触发方式怎么接（Siri、快捷指令、菜单栏、手机）：docs/TRIGGERS.md
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile

from . import inbox
from .app import Session
from .dispatcher import Dispatcher, TaskState
from .notify import MacNotifier, NtfyNotifier
from .planner import Planner
from .workers import ClaudeCodeWorker, LocalWorker

READBACK_SECONDS = 3


def indent(s: str, n: int = 6) -> str:
    return "\n".join(" " * n + line for line in s.strip().splitlines()[:40])


def build(args):
    mac = MacNotifier()
    notifiers = [mac]
    ntfy = NtfyNotifier(args.ntfy) if args.ntfy else None
    if ntfy:
        notifiers.append(ntfy)

    def on_change(st: TaskState):
        tail = f"\n{indent(st.result)}" if st.status in ("done", "draft", "failed") else ""
        print(f"  [{st.task.id}] {st.status}{tail}")

    disp = Dispatcher(
        workers={"claude_code": ClaudeCodeWorker(args.claude_bin, cwd=args.cwd), "local": LocalWorker()},
        notifiers=notifiers, on_change=on_change)
    session = Session(disp, Planner(), say=mac.say)
    return session, ntfy


async def interactive(session: Session, text: str) -> None:
    """终端里派活：先念回来，给三秒打断。口令直接执行。"""
    tl = session.plan_only(text) if not _is_command(text) else None
    if tl is None:
        print(session.handle(text)); return
    if not tl.tasks:
        print(tl.say); return
    print(f"  {tl.say}")
    session.say(tl.say)
    if sys.stdin.isatty():
        print(f"  {READBACK_SECONDS} 秒内回车取消…", end="", flush=True)
        try:
            await asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline),
                                   READBACK_SECONDS)
            print(" 取消了"); return
        except asyncio.TimeoutError:
            print(" 开始")
    print("  派了：" + "、".join(session.disp.submit(tl)))


def _is_command(text: str) -> bool:
    from .app import _CMD
    return bool(_CMD.match(text.strip()))


async def main_async(args) -> int:
    session, ntfy = build(args)
    loop = asyncio.get_event_loop()
    if ntfy:
        ntfy.listen(lambda msg: print("\n  [手机] " + session.handle(msg)), loop)

    if args.text:
        await interactive(session, args.text)
        await session.disp.wait_all()
        return 0

    if args.serve:
        inbox.start(session, loop, args.port)
        print(f"收件口开在 http://127.0.0.1:{args.port}/say" + (f"，手机走 ntfy topic {args.ntfy}-in" if ntfy else ""))
        print("Ctrl-C 退出。")
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            pass
        return 0

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
            if text and text.strip():
                await interactive(session, text)
    except (KeyboardInterrupt, EOFError):
        print()
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="voice_router", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--text", "-t", help="只派这一句，跑完退出")
    p.add_argument("--serve", action="store_true", help="常驻后台，开本机收件口")
    p.add_argument("--port", type=int, default=8765, help="收件口端口")
    p.add_argument("--listen", action="store_true", help="用麦克风")
    p.add_argument("--ntfy", help="ntfy topic：推手机，也从手机收")
    p.add_argument("--claude-bin", default="claude")
    p.add_argument("--cwd", default=None, help="claude -p 的工作目录")
    p.add_argument("--stt-model", default="small")
    args = p.parse_args(argv)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
