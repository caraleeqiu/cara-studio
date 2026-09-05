"""按住说话，终端版：回车开始，再回车结束。

不做唤醒词。唤醒词误触发多、要常驻听，等硬件当输入端时再考虑。
"""

from __future__ import annotations

import threading
import wave

RATE = 16000     # whisper 就要 16k 单声道


def record(path: str) -> str:
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as e:
        raise SystemExit("要用麦克风得先装：pip install sounddevice numpy") from e

    chunks: list = []
    stop = threading.Event()

    def cb(indata, frames, time, status):
        chunks.append(indata.copy())

    input("回车开始录音…")
    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", callback=cb):
        input("说完按回车。")
        stop.set()

    audio = np.concatenate(chunks) if chunks else np.zeros((0, 1), dtype="int16")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(audio.tobytes())
    return path
