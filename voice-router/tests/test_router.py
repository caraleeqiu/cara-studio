"""离线测试：不碰网络、不碰硬件。"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voice_router.brain import Brain            # noqa: E402
from voice_router.routes import Routes           # noqa: E402
from voice_router.schema import COMMAND_SCHEMA, Arg, Command   # noqa: E402
from voice_router.sinks import Dispatcher, encode  # noqa: E402

ROUTES = Routes.load(ROOT / "routes.json")


class TestRoutes(unittest.TestCase):
    def test_keyword_light_on_off(self):
        self.assertEqual(ROUTES.keyword_route("开灯").arg_dict(), {"state": "on"})
        self.assertEqual(ROUTES.keyword_route("把灯关了").arg_dict(), {"state": "off"})

    def test_keyword_music(self):
        self.assertEqual(ROUTES.keyword_route("下一首歌").arg_dict(), {"action": "next"})

    def test_unknown_goes_to_chat(self):
        c = ROUTES.keyword_route("今天天气怎么样")
        self.assertEqual(c.intent, "chat")
        self.assertEqual(c.arg_dict()["text"], "今天天气怎么样")

    def test_validate_rejects_unknown_intent(self):
        bad = Command(intent="teleport", args=[], say="走", confidence=0.9)
        fixed = ROUTES.validate(bad, "带我走")
        self.assertEqual(fixed.intent, "chat")
        self.assertLessEqual(fixed.confidence, 0.2)

    def test_describe_lists_every_intent(self):
        d = ROUTES.describe()
        for i in ROUTES.intents:
            self.assertIn(f"- {i.name}", d)

    def test_sink_lookup(self):
        self.assertEqual(ROUTES.sink_for("light"), "device")
        self.assertEqual(ROUTES.sink_for("chat"), "console")
        self.assertEqual(ROUTES.sink_for("nope"), "console")


class TestSchema(unittest.TestCase):
    def test_wire_shape(self):
        c = Command(intent="light", args=[Arg(name="state", value="on")], say="好", confidence=0.9)
        self.assertEqual(json.loads(encode(c)), {"intent": "light", "args": {"state": "on"}})

    def test_schema_is_strict(self):
        self.assertFalse(COMMAND_SCHEMA["additionalProperties"])
        self.assertEqual(set(COMMAND_SCHEMA["required"]), set(COMMAND_SCHEMA["properties"]))

    def test_model_output_roundtrip(self):
        raw = '{"intent":"light","args":[{"name":"color","value":"red"}],"say":"红的","confidence":0.95}'
        c = Command.model_validate(json.loads(raw))
        self.assertEqual(c.arg_dict(), {"color": "red"})


class TestBrain(unittest.TestCase):
    def test_offline_uses_keywords(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            b = Brain(ROUTES)
        self.assertFalse(b.live)
        self.assertEqual(b.route("开灯").intent, "light")

    def test_live_parses_model_json_and_validates(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x"}):
            b = Brain(ROUTES)
        fake = mock.Mock()
        fake.stop_reason = "end_turn"
        fake.content = [mock.Mock(type="text", text=json.dumps(
            {"intent": "mode", "args": [{"name": "name", "value": "night"}], "say": "夜间", "confidence": 0.8}))]
        with mock.patch.object(Brain, "client", new_callable=mock.PropertyMock) as client:
            client.return_value.beta.messages.create.return_value = fake
            c = b.route("切到夜间模式")
            kwargs = client.return_value.beta.messages.create.call_args.kwargs
        self.assertEqual(c.intent, "mode")
        self.assertEqual(c.arg_dict(), {"name": "night"})
        self.assertEqual(kwargs["fallbacks"], "default")
        self.assertEqual(kwargs["output_config"]["format"]["schema"], COMMAND_SCHEMA)

    def test_live_failure_falls_back(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x"}):
            b = Brain(ROUTES)
        with mock.patch.object(Brain, "client", new_callable=mock.PropertyMock) as client:
            client.return_value.beta.messages.create.side_effect = RuntimeError("boom")
            c = b.route("开灯")
        self.assertEqual(c.intent, "light")
        self.assertLess(c.confidence, 0.5)


class TestDispatch(unittest.TestCase):
    def test_dry_run_never_opens_hardware(self):
        d = Dispatcher(ROUTES, dry_run=True)
        c = Command(intent="light", args=[Arg(name="state", value="on")], say="好", confidence=0.9)
        self.assertIsNone(d.dispatch(c))

    def test_unreachable_sink_degrades_to_console(self):
        d = Dispatcher(ROUTES)              # /dev/ttyUSB0 在这里不存在
        c = Command(intent="light", args=[], say="好", confidence=0.9)
        self.assertIsNone(d.dispatch(c))
        self.assertIs(d.sink("device"), d.sink("console"))


class TestSerialWire(unittest.TestCase):
    """用伪终端模拟板子：收一行 JSON，回一行 ack。"""

    def test_roundtrip_over_pty(self):
        import pty
        import threading
        from voice_router.sinks import SerialSink

        master, slave = pty.openpty()
        sink = SerialSink(os.ttyname(slave), timeout=2)
        got = {}

        def board():
            buf = b""
            while b"\n" not in buf:
                buf += os.read(master, 256)
            got["line"] = buf.split(b"\n")[0].decode()
            os.write(master, b'{"ok":true,"intent":"light"}\n')

        t = threading.Thread(target=board, daemon=True); t.start()
        c = Command(intent="light", args=[Arg(name="state", value="on")], say="好", confidence=0.9)
        ack = sink.send(c)
        t.join(2)
        self.assertEqual(json.loads(got["line"]), {"intent": "light", "args": {"state": "on"}})
        self.assertEqual(json.loads(ack), {"ok": True, "intent": "light"})


if __name__ == "__main__":
    unittest.main()
