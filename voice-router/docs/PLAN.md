# 语音派活：方案研究

目标一句话：**你用嘴派活，它调度几个 App 和 Agent 并行去干，干完推给你。**
最后把「按键说话」换成一个外接硬件。

日期：2026-09-05。这份文档只定方案，不写代码。第二版，按「派活」的场景重写。

---

## 0. 定位

第一版把它当成「用嘴驱动的启动器」，切 App、听写、点界面。你给的例子把需求纠正了：

> 打开 Claude Code，帮我查个东西，查好了推我一条。同时打开 Gmail，把某某事办了。

这不是启动器，是**调度器**。启动器一次干一件事、当场干完。调度器把一句话拆成几件事，
派给不同的 worker，它们各干各的，谁干完谁汇报。语音只是派活的方式。

这个东西市面上没有现成的。Siri 只能单步，Raycast 只能跑预设脚本，Claude Code 本身要你坐在终端前。
**要自己做的是那个调度层**，worker 都是现成的。

---

## 1. 核心场景走一遍

把你那句话按时间线拆开，看每一步谁在干：

| 时刻 | 发生什么 | 谁干 |
|---|---|---|
| 0s | 按住键说：「打开 Claude Code 查一下 X，查好推我。同时打开 Gmail 把 Y 回了」 | 你 |
| 1s | 语音变文字 | 本地识别 |
| 2s | 文字拆成两个任务：A「用 Claude Code 查 X，完成后通知」、B「用 Gmail 回 Y」 | Claude 抽结构 |
| 2s | 屏幕上弹出两条任务卡，念一句「两件事，开始了」 | 调度器 |
| 2s | A 和 B **同时**起两个 Claude Code 会话 | 调度器 |
| 40s | B 先干完：Gmail 那封回好了（发之前停下来问你一句） | worker B |
| 90s | A 干完：查到了，结果三行 | worker A |
| 90s | Mac 弹通知，手机也收一条，桌面任务卡变绿 | 通知 |
| 随时 | 你问「查完了吗」，它答「A 还在跑，B 好了」 | 调度器 |

关键观察：**A 和 B 都不需要「打开」任何窗口。** Claude Code 有程序接口，Gmail 也有。
「打开 App」是人的习惯，程序不用打开就能干。想看着它干也可以开一个窗口，那是展示，不是必需。

---

## 2. 架构

```
 说话 ──► 本地语音识别 ──► 拆任务（Claude，输出 JSON）──► 调度器
                                                         │
                          ┌──────────────────────────────┼──────────────────────┐
                          ▼                              ▼                      ▼
                   worker：Claude Code            worker：本地动作          worker：点界面
                   （查资料、写东西、               （切 App、听写、          （没接口的 App，
                     Gmail、日历、文件）              开网页、跑脚本）           兜底用）
                          │                              │                      │
                          └──────────────► 完成 ◄────────┴──────────────────────┘
                                             │
                                   Mac 通知 + 手机推送 + 任务卡
```

原则只有一条：**能走接口就不点界面。** 接口稳、快、便宜，点界面慢、贵、会点错。
Claude Code 的接口是 `claude -p`，Gmail 的接口是 Claude Code 里的 Gmail 连接器。
点界面（辅助功能树加截图）留给真没有接口的 App，第一版不做。

---

## 3. 语音识别：走本地

和第一版结论一样，Actionway 不适合这一层，它的转写是给媒体文件用的。

| 方案 | 条件 | 中文 | 延迟 | 成本 |
|---|---|---|---|---|
| **Apple SpeechAnalyzer** | macOS 26 | 普通话、粤语 | 最快 | 0 |
| **whisper.cpp** | 任意 Apple Silicon | 好 | 短句 0.5 到 1 秒 | 0 |

派活的句子比听写长，一句二三十字，两种识别都够用。**要你确认 macOS 版本。**

---

## 4. 拆任务：Claude 结构化输出

一句话进来，Claude 输出一个任务列表，形状固定：

```json
{
  "tasks": [
    { "id": "a", "worker": "claude_code", "instruction": "查一下 X，给我三行结论",
      "notify": true, "needs_confirm": false },
    { "id": "b", "worker": "claude_code", "instruction": "用 Gmail 找到某某的最新一封邮件，回复 Y",
      "notify": true, "needs_confirm": true }
  ],
  "say": "两件事，开始了"
}
```

这就是现在 `voice_router/` 里那套东西，把 `Command` 换成 `TaskList`，路由表换成 worker 表。
`needs_confirm` 由模型判断：发邮件、删东西、付钱、发消息给别人，一律 true。

---

## 5. worker：三类

### 5.1 Claude Code（主力）

派活里八成的事都能交给它：查资料、写东西、看文件、Gmail、日历、Drive。

```bash
claude -p "查一下 X，给我三行结论" --output-format json
```

- 返回 JSON，`result` 字段是答案，`session_id` 能续。
- 并行就是同时起几个进程，互不干扰。
- Gmail 走 Claude Code 里的 Gmail 连接器（claude.ai 的 connectors，`/mcp` 里接）。
  不用自己搞 Google OAuth 那一套。
- 权限：`--permission-mode` 控制它能自己干多少。查东西给 `auto`，动邮件的任务让它停在发送前。
- 想看着它干：调度器可以同时开一个终端窗口 `--resume` 那个会话，纯展示。

登录：`claude -p` 用你的 Claude Code 订阅登录。Python 的 Agent SDK 官方文档要求 API key，
所以**第一版直接 shell 出去调 `claude -p`**，不用 SDK。够用，而且不多花钱。

### 5.2 本地动作（秒回的）

切 App、听写上屏、开网址、跑一条脚本。不走模型，调度器自己做：

- 切 App：`open -a WeChat`
- 听写：文本进剪贴板，发 Cmd+V，再把原剪贴板还回去。中文稳。
- 开网址：`open https://...`

### 5.3 点界面（兜底，第一版不做）

真没有接口的 App，用 [macos-use](https://macos-use.dev/) 读辅助功能树按名字点，截图兜底。
第一版不做，因为你举的例子里一个都不需要。什么时候有一个具体的 App 需要它再加。

---

## 6. 通知与回传

| 渠道 | 怎么做 | 什么时候用 |
|---|---|---|
| Mac 通知 | `osascript -e 'display notification ...'` 一行 | 每个任务完成 |
| 手机推送 | [ntfy](https://ntfy.sh/)：一条 curl，iOS 有 App，免费。国内常用 Bark 也行 | 你不在电脑前 |
| 任务卡 | 桌面一个小浮窗，每个任务一行，跑着的黄、完了的绿、等确认的红 | 一直在 |
| 念出来 | macOS `say` 命令，或者不念只弹 | 短结论 |
| 问进度 | 「查完了吗」也是一句派活，worker 是调度器自己 | 随时 |

第一版做 Mac 通知和任务卡。手机推送加一个 ntfy 的 topic 就有了，十分钟的事。

---

## 7. 安全

worker 在替你发邮件、动文件，这块不能后补。

- **`needs_confirm` 的任务在最后一步停下来**。邮件写好了，弹出来给你看，你说「发」它才发。
  发送、删除、付款、给别人发消息，永远确认。
- **每个 worker 一个权限档**。查资料的会话只读；动邮件的会话只能动邮件。
  靠 `claude -p` 的 `--allowedTools` 和 `--permission-mode` 控。
- **一键停**。Esc 杀掉所有在跑的会话。
- 识别错了会派错活。拆任务之后先念一遍「两件事：查 X，回 Y」，三秒内没打断才开始。
  这三秒比事后收拾便宜得多。

---

## 8. 形态

| 阶段 | 形态 |
|---|---|
| 现在 | Python 脚本，终端里跑。复用 `voice-router/`，加调度器和 `claude -p` worker |
| 稳定后 | Swift 菜单栏小程序，任务卡做成浮窗，全局快捷键 |

---

## 9. 硬件

硬件只换一环：**触发**。

- 最简单：ESP32 一个按钮，蓝牙模拟成键盘，按下发一个键，Mac 零改动。
- 进一步：盒子自带麦克风，离嘴近，识别率高。
- 再进一步：盒子有小屏，任务卡显示在盒子上，确认按钮也在盒子上。
  你不在电脑前，盒子还能替手机推送。

现在仓库里的 ESP32 固件是「Mac 发命令给板子」，方向反了，硬件阶段重写成「板子发触发给 Mac」。

---

## 10. 待你决定

1. **macOS 版本**是不是 26。
2. **Claude Code 里 Gmail 连接器接了没有**。没接的话先接，`/mcp` 里操作。
3. **第一批想派的三件事**。拿真实需求测，比编例子准。
4. **手机推送要不要**。要的话装 ntfy 或 Bark。
5. 派活之后**要不要看着它干**。要的话调度器多开一个窗口，纯展示。

定了我就把 `voice-router/` 改成调度器：`Command` 换 `TaskList`，加 `claude -p` worker，
加 Mac 通知。第一版目标是你那句话能真跑通。

---

## 参考

- `claude -p` 非交互模式：https://code.claude.com/docs/en/headless
- Python Agent SDK：https://code.claude.com/docs/en/agent-sdk/python
- SpeechAnalyzer：https://blog.addpipe.com/apple-speechanalyzer-api/
- ntfy：https://ntfy.sh/
- macos-use（兜底用）：https://macos-use.dev/
