# voice-router

说一句、走开、回来点头。一句话拆成几件事，派给不同 worker 并行干，干完推到 Mac 和手机，
要发出去的东西先给你看、随便改、你说「发」才发。

方案和为什么这么做：[docs/PLAN.md](docs/PLAN.md)。

```
说话 ──► 本地识别 ──► 拆任务(Claude, JSON) ──► 调度器 ──┬─► claude -p  (查、写、Gmail、文件)
                                                     ├─► 本地动作   (切 App、听写、开网址)
                                                     └─► 通知       (Mac 弹窗 + ntfy 手机推送，手机上能点「发」)
```

## 跑起来

```bash
cd voice-router
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # 拆任务用。没有就按连接词切句，能演不能用
which claude                         # worker 用你本机的 Claude Code，走它的登录

python -m voice_router --text "查一下明天上海天气，查好推我，同时用 Gmail 回复老张说周五可以"
python -m voice_router               # 交互模式，每行一句
python -m voice_router --listen      # 麦克风，回车开始 / 结束（要 pip install faster-whisper sounddevice numpy）
python -m voice_router --ntfy 你的topic   # 手机推送，通知上有「发 / 算了」按钮，手机上也能派活
python -m voice_router --serve --ntfy 你的topic   # 常驻后台，开本机收件口。Siri / 快捷指令 / 菜单栏都投这里
```

**入口不是 Claude。** 调度器常驻后台，Siri、快捷指令、菜单栏图标、手机都只是往收件口投一句话。
怎么接：[docs/TRIGGERS.md](docs/TRIGGERS.md)。

派活之后的口令，打字或说都行：

| 口令 | 干什么 |
|---|---|
| `进度` | 所有活的状态 |
| `看 b` | b 的草稿全文 |
| `发 b` | 确认执行最后一步 |
| `改 b 语气软一点` | 同一个会话续着改，改完再给你看 |
| `算了 b` | 作废 |

只有一份草稿时不用报 id。

## 它怎么保证不乱发

- 拆完先念回来「2 件事：…」，三秒内回车取消。识别错了派错活比等三秒贵。
- 发邮件、发消息、删、付款的活，worker 只准备不执行：写好全文给你看，能存草稿就存在 App 里。
- 你说「发」它才 `--resume` 那个会话执行最后一步。没说永远不发，不超时。
- 手机上的「发」按钮走 ntfy 的回执 topic，Mac 不用暴露在公网。

## 没有 Mac 也能开发

不是 Mac 时本地动作只打印不执行，通知打到终端。`tests/fake_claude.py` 是假的 `claude`，
`--claude-bin tests/fake_claude.py` 就能把整条链路跑通：

```bash
python -m voice_router --claude-bin tests/fake_claude.py --text "查 X 同时回复老张"
python -m unittest discover -s tests -v
```

## 文件

```
voice_router/
  app.py         Session：所有入口最后都调它的 handle(text)
  inbox.py       本机 HTTP 收件口，给 Siri / 快捷指令 / 菜单栏投话
  planner.py     一句话 → TaskList（Claude 结构化输出，兜底按连接词切）
  dispatcher.py  状态机 + 并行 + 确认循环
  workers.py     claude -p / 本地动作
  notify.py      Mac 弹窗、ntfy 推送与手机回执
  schema.py      Task / TaskList 契约
  listen.py stt.py   麦克风、本地识别
  brain.py routes.py sinks.py   第一版的硬件路由，硬件阶段再用
firmware/esp32/  第一版固件（方向要反过来，硬件阶段重写）
tools/menubar.py 菜单栏小图标，模拟交付形态
docs/PLAN.md     方案
docs/TRIGGERS.md 触发方式：Siri、快捷指令、菜单栏、手机、开机自启
```

## 接下来

- 交付形态：Swift 菜单栏小程序，任务卡浮窗，全局快捷键。Python 只用来验证链路。
- 硬件：ESP32 蓝牙键盘按钮当触发，再往后是带麦克风和小屏的盒子。
