# voice-router

一句话进来，变成一条结构化命令，发到该去的地方。独立小项目，和外面的作品集站无关。

```
麦克风 ──► 本地语音识别 ──► Claude 抽意图 ──► 分发 ──► 终端 / 串口 / MQTT ──► 板子
          (faster-whisper)   (结构化 JSON)    (查路由表)
```

中间那条 JSON 是整个东西的契约，三边都只认它：

```json
{"intent": "light", "args": {"state": "on", "color": "red"}, "say": "红的", "confidence": 0.95}
```

发给硬件时只留 `intent` 和 `args`，一行一条。

## 跑起来

```bash
cd voice-router
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # 没有也能跑，退到关键词匹配

python -m voice_router --text "开灯" --dry-run
python -m voice_router --text "灯变成红色，暗一点" --dry-run
```

`--dry-run` 把所有出口都打到终端，板子没插也能看整条链路。

要用麦克风：

```bash
pip install faster-whisper sounddevice numpy
python -m voice_router --dry-run          # 回车开始，说完再回车
```

第一次会下载 whisper small 模型，几百兆。识别在本地跑，不出网。

## 改路由

全部在 `routes.json`，不用碰代码：

- `intents`：每个意图一条。`desc` 和 `examples` 是给模型看的，写清楚它就分得准。`keywords` 是没模型时的兜底。`sink` 指定这个意图发到哪个出口。
- `sinks`：出口定义。`console` 打终端，`serial` 走 USB 串口，`mqtt` 走 broker。
- 必须保留一个叫 `chat` 的意图，模型拿不准的都归它。

串口示例：

```json
"device": { "type": "serial", "port": "/dev/ttyUSB0", "baud": 115200 }
```

MQTT 示例：

```json
"device": { "type": "mqtt", "host": "broker.emqx.io", "topic": "voice/cmd" }
```

出口连不上会自动降级到终端并打一行提示，主循环不会挂。

## 硬件端

`firmware/esp32/esp32.ino`。串口 115200，读一行 JSON，按 `intent` 执行，回一行 `{"ok":true}`。
默认只点板载 LED，想接灯带把 `USE_NEOPIXEL` 打开。走 MQTT 的话把串口读那段换成 PubSubClient 订阅，处理函数一行不用改。

## 测试

```bash
python -m unittest discover -s tests -v
```

全部离线，不碰网络不碰硬件。

## 为什么这么切

- **识别和理解分开**。Claude 不吃音频，whisper 本地跑又便宜又不出网，短指令 small 模型够用。
- **模型只做翻译，不做执行**。它输出 JSON，执行是代码查表。换硬件、换协议，模型那边一个字不用改。
- **没 key 也能演**。关键词兜底会明说自己在兜底，不装作听懂了。
- **意图表可以小**。四个够起步。加一个意图就是往 `routes.json` 加一条，加一个出口就是在 `sinks.py` 加一个类。
