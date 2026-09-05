"""语音识别。本地跑 faster-whisper，不出网，树莓派也能扛 small 模型。

没装 faster-whisper 时 transcribe 会直接报错说明怎么装，
--text 模式不经过这里。
"""

from __future__ import annotations


class STT:
    def __init__(self, model_size: str = "small", language: str = "zh"):
        self.language = language
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise SystemExit("要用麦克风得先装：pip install faster-whisper sounddevice numpy") from e
        # int8 在 CPU 上最省，识别质量对短指令够用
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, wav_path: str) -> str:
        segments, _ = self.model.transcribe(wav_path, language=self.language, beam_size=1,
                                            vad_filter=True)
        return "".join(s.text for s in segments).strip()
