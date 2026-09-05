# 触发方式：Claude 不是入口

调度器常驻后台，开一个收件口。任何能往里投一句话的东西都是入口。
Claude Code 只是被它叫起来干活的，你永远不用打开它。

```
Siri / 快捷指令 ──┐
菜单栏小图标 ─────┤
手机 ntfy ────────┼──► 收件口 ──► 调度器 ──► claude -p / 本地动作
键盘快捷键 ───────┤
实体按钮（以后）──┘
```

先把调度器跑起来：

```bash
cd voice-router
python -m voice_router --serve --ntfy 你的topic
# 收件口开在 http://127.0.0.1:8765/say
```

收件口就四个口子，`curl` 就能试：

```bash
curl -X POST localhost:8765/say -d "查一下明天上海天气，查好推我"
curl localhost:8765/status
curl -X POST localhost:8765/confirm/a
curl -X POST localhost:8765/revise/a -d "语气软一点"
```

`/say` 返回念回去的那句，Siri 会把它读出来。

---

## 1. Siri（Mac 上）

用「快捷指令」App 建一个，五步：

1. 新建快捷指令，起名 **派活**。名字就是 Siri 的唤醒词，「嘿 Siri，派活」。
2. 加动作 **听写文本**。语言选中文。这一步 Siri 帮你做语音识别，免费、本地。
3. 加动作 **获取 URL 内容**：URL 填 `http://127.0.0.1:8765/say`，方法 POST，
   请求体选「文件」，把上一步的「听写文本」拖进去。
4. 加动作 **朗读文本**，内容是上一步的返回。它会念「2 件事：查天气，回老张」。
5. 快捷指令设置里勾上「在菜单栏显示」，顺手给它配个键盘快捷键。

这样一条路：说「嘿 Siri，派活」 → Siri 问你 → 你说一句 → 它念回来 → 后台开始干。
不开任何窗口。

口令也走这条：「嘿 Siri，派活」→「发 b」。

## 2. Siri（iPhone 上）

手机上 Siri 到不了你 Mac 的 127.0.0.1，走 ntfy 中转。同样建一个快捷指令：

1. **听写文本**。
2. **获取 URL 内容**：URL 填 `https://ntfy.sh/你的topic-in`，方法 POST，请求体是听写文本。
3. Mac 上的调度器订阅着 `你的topic-in`，收到就派活，结果推回 `你的topic`，手机 ntfy App 会响。

这条路的意思是：**人在外面也能派活**，回家之前先把邮件写好放着等你点头。
`-in` topic 谁都能往里发，所以 topic 名要长、要随机，或者用 ntfy 的私有 topic。

## 3. 菜单栏小图标（模拟的 App）

`tools/menubar.py` 是一个最小的菜单栏程序：一个图标，点开有「说一句」和「进度」。
「说一句」弹一个输入框，打字或者按 Mac 自带的听写快捷键说话，回车就投进收件口。

```bash
pip install rumps
python tools/menubar.py
```

这个是给你摸一摸交付形态长什么样的。真正交付会用 Swift 重写，但交互就是这样：
一个图标，一个快捷键，一个任务卡。

## 4. 键盘快捷键

最简单的做法是上面快捷指令的键盘快捷键。
按住说话那种体验（按下开始录、松开结束）要菜单栏程序监听全局按键，Swift 版做。

## 5. 手机上确认

不用建任何东西。调度器推到手机的通知自带「Send / Cancel」两个按钮，
点了走 `-in` topic 回来。走开之后邮件写好了，手机上看一眼点一下就发。

## 6. 开机自启

调度器做成 launchd 的用户代理，登录就起，不用开终端。

```bash
cat > ~/Library/LaunchAgents/ai.cara.voice-router.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.cara.voice-router</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/env</string><string>python3</string>
    <string>-m</string><string>voice_router</string>
    <string>--serve</string><string>--ntfy</string><string>你的topic</string>
  </array>
  <key>WorkingDirectory</key><string>/绝对路径/cara-studio/voice-router</string>
  <key>EnvironmentVariables</key><dict>
    <key>ANTHROPIC_API_KEY</key><string>填你的</string>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/voice-router.log</string>
  <key>StandardErrorPath</key><string>/tmp/voice-router.log</string>
</dict></plist>
PLIST
launchctl load ~/Library/LaunchAgents/ai.cara.voice-router.plist
```

PATH 里要能找到 `claude`，不然 worker 起不来。`which claude` 看它在哪。

## 7. 实体按钮（硬件阶段）

ESP32 用蓝牙模拟成键盘，按下发一个快捷键，触发第 1 节的快捷指令。Mac 侧零改动。
再往后盒子带麦克风，录音传给 Mac，走本地识别再投收件口。
