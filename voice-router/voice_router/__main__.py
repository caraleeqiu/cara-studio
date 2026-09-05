"""入口。

  python -m voice_router --text "开灯"         # 不用麦克风，直接喂文字
  python -m voice_router                        # 麦克风，回车开始/结束
  python -m voice_router --dry-run              # 全部打到终端，不碰硬件
  python -m voice_router --routes my.json       # 换一张路由表
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from .brain import Brain
from .routes import Routes
from .sinks import Dispatcher

HERE = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="voice_router", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--text", "-t", help="跳过麦克风，直接路由这句话")
    p.add_argument("--wav", help="路由一个已有的 wav 文件")
    p.add_argument("--routes", default=str(HERE / "routes.json"), help="路由表路径")
    p.add_argument("--dry-run", action="store_true", help="所有出口都打到终端")
    p.add_argument("--stt-model", default="small", help="faster-whisper 模型大小")
    a = p.parse_args(argv)

    routes = Routes.load(a.routes)
    brain = Brain(routes)
    out = Dispatcher(routes, dry_run=a.dry_run)

    def handle(text: str):
        print(f"听到：{text}")
        cmd = brain.route(text)
        print(f"意图：{cmd.intent}  参数：{cmd.arg_dict()}  信心：{cmd.confidence:.2f}")
        print(f"回答：{cmd.say}")
        ack = out.dispatch(cmd)
        if ack:
            print(f"  ← {ack}")

    if a.text:
        handle(a.text)
        return 0

    from .stt import STT
    stt = STT(a.stt_model, routes.language)

    if a.wav:
        handle(stt.transcribe(a.wav))
        return 0

    from .listen import record
    tmp = os.path.join(tempfile.gettempdir(), "voice_router_last.wav")
    print("Ctrl-C 退出。")
    try:
        while True:
            record(tmp)
            handle(stt.transcribe(tmp))
            print()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
