"""出口。每个 sink 就一个 send(cmd)。

线上格式统一：一行 JSON 加换行，{"intent": "...", "args": {...}}。
串口和 MQTT 发的是同一个东西，硬件端只要会读一行 JSON 就行。
"""

from __future__ import annotations

import json
import sys

from .schema import Command


def encode(cmd: Command) -> str:
    return json.dumps(cmd.wire(), ensure_ascii=False)


class ConsoleSink:
    name = "console"

    def send(self, cmd: Command) -> str | None:
        print(f"  → {encode(cmd)}")
        return None


class SerialSink:
    """USB 串口直连板子。发一行，等板子回一行 ack（可以没有）。"""
    name = "serial"

    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0):
        try:
            import serial
        except ImportError as e:
            raise SystemExit("串口出口要装：pip install pyserial") from e
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def send(self, cmd: Command) -> str | None:
        self.ser.write((encode(cmd) + "\n").encode("utf-8"))
        self.ser.flush()
        ack = self.ser.readline().decode("utf-8", "replace").strip()
        return ack or None


class MqttSink:
    """走 broker。板子在哪都行，手机上也能发。"""
    name = "mqtt"

    def __init__(self, host: str, port: int = 1883, topic: str = "voice/cmd",
                 username: str | None = None, password: str | None = None):
        try:
            import paho.mqtt.client as mqtt
        except ImportError as e:
            raise SystemExit("MQTT 出口要装：pip install paho-mqtt") from e
        self.topic = topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if username:
            self.client.username_pw_set(username, password)
        self.client.connect(host, port, keepalive=30)
        self.client.loop_start()

    def send(self, cmd: Command) -> str | None:
        info = self.client.publish(self.topic, encode(cmd), qos=1)
        info.wait_for_publish(timeout=3)
        return "published" if info.is_published() else "publish timeout"


def build(cfg: dict):
    kind = cfg.get("type", "console")
    opts = {k: v for k, v in cfg.items() if k != "type"}
    if kind == "console":
        return ConsoleSink()
    if kind == "serial":
        return SerialSink(**opts)
    if kind == "mqtt":
        return MqttSink(**opts)
    raise ValueError(f"不认识的 sink 类型：{kind}")


class Dispatcher:
    """按意图查表挑出口。出口连不上就降级到终端，主循环不能因为板子没插而死。"""

    def __init__(self, routes, dry_run: bool = False):
        self.routes = routes
        self.dry_run = dry_run
        self._sinks: dict = {"console": ConsoleSink()}

    def sink(self, name: str):
        if self.dry_run:
            return self._sinks["console"]
        if name not in self._sinks:
            cfg = self.routes.sinks.get(name, {"type": "console"})
            try:
                self._sinks[name] = build(cfg)
            except Exception as e:
                print(f"[sink] {name} 连不上（{e}），先打到终端", file=sys.stderr)
                self._sinks[name] = self._sinks["console"]
        return self._sinks[name]

    def dispatch(self, cmd: Command) -> str | None:
        return self.sink(self.routes.sink_for(cmd.intent)).send(cmd)
