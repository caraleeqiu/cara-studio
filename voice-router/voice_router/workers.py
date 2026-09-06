"""worker：真正干活的。

- ClaudeCodeWorker：shell 出去调 `claude -p`，走用户的 Claude Code 登录。
  需要确认的活只准备草稿，不准执行最后一步；确认时 --resume 同一个会话说「发」。
- LocalWorker：切 App、开网址、听写上屏。不走模型，秒回。
"""

from __future__ import annotations

import asyncio
import json
import platform
import shutil
import sys
from dataclasses import dataclass

from .schema import Task


@dataclass
class Result:
    text: str
    session_id: str | None = None
    ok: bool = True


DRAFT_SUFFIX = (
    "\n\n重要：这件事的最后一步（发送 / 提交 / 删除 / 付款）不要做。"
    "把准备好的完整内容原样输出给我看：如果是邮件，输出收件人、标题、正文全文。"
    "如果能在对应 App 里存成草稿（比如 Gmail 草稿），就存草稿并告诉我草稿在哪。"
    "等我说「发」再执行。"
)
REVISE_PREFIX = "改一下："
REVISE_SUFFIX = "\n\n改完把新版本全文输出给我看，仍然不要执行最后一步。"
CONFIRM_TEXT = "确认。现在执行最后一步（发送 / 提交），如果之前存了草稿就发那份草稿。做完回一句确认。"


class ClaudeCodeWorker:
    name = "claude_code"

    def __init__(self, claude_bin: str = "claude", cwd: str | None = None,
                 timeout: float = 600, permission_mode: str = "auto"):
        self.bin = claude_bin
        self.cwd = cwd
        self.timeout = timeout
        self.permission_mode = permission_mode
        if shutil.which(claude_bin) is None:
            print(f"[worker] 找不到 {claude_bin}，claude_code 的活会失败。", file=sys.stderr)

    async def run(self, task: Task) -> Result:
        prompt = task.instruction
        if task.app:
            prompt += f"\n\n用 {task.app} 办这件事。能走接口或脚本就不要开窗口。"
        if task.needs_confirm:
            prompt += DRAFT_SUFFIX
        return await self._call(prompt)

    async def revise(self, session_id: str, text: str) -> Result:
        return await self._call(REVISE_PREFIX + text + REVISE_SUFFIX, resume=session_id)

    async def confirm(self, session_id: str) -> Result:
        return await self._call(CONFIRM_TEXT, resume=session_id)

    async def _call(self, prompt: str, resume: str | None = None) -> Result:
        cmd = [self.bin, "-p", prompt, "--output-format", "json",
               "--permission-mode", self.permission_mode, "--permission-prompts", "none"]
        if resume:
            cmd += ["--resume", resume]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=self.cwd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, err = await asyncio.wait_for(proc.communicate(), self.timeout)
        except FileNotFoundError:
            return Result(text=f"找不到 {self.bin}", ok=False)
        except asyncio.TimeoutError:
            proc.kill()
            return Result(text="超时了", ok=False)

        raw = out.decode("utf-8", "replace").strip()
        try:
            j = json.loads(raw)
        except json.JSONDecodeError:
            # 没拿到 JSON，多半是没登录或参数不对，把 stderr 带回来
            msg = raw or err.decode("utf-8", "replace").strip() or f"exit {proc.returncode}"
            return Result(text=msg[:2000], ok=False)
        text = j.get("result") or j.get("error") or ""
        return Result(text=str(text), session_id=j.get("session_id"),
                      ok=proc.returncode == 0 and not j.get("is_error", False))


class LocalWorker:
    """Mac 上真干；别的系统只打印要干什么，方便在别处开发。"""
    name = "local"

    def __init__(self):
        self.mac = platform.system() == "Darwin"

    async def run(self, task: Task) -> Result:
        fn = {"switch_app": self.switch_app, "open_url": self.open_url,
              "dictate": self.dictate}.get(task.action)
        if fn is None:
            return Result(text=f"不认识的本地动作：{task.action}", ok=False)
        return await fn(task.instruction)

    async def _sh(self, *cmd) -> Result:
        if not self.mac:
            return Result(text="（非 Mac，只演不做）" + " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE)
        _, err = await proc.communicate()
        return Result(text=err.decode().strip() or "好了", ok=proc.returncode == 0)

    async def switch_app(self, app: str) -> Result:
        return await self._sh("open", "-a", app)

    async def open_url(self, url: str) -> Result:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return await self._sh("open", url)

    async def dictate(self, text: str) -> Result:
        """文本进剪贴板，发 Cmd+V。中文、emoji、长段都稳。"""
        if not self.mac:
            return Result(text="（非 Mac，只演不做）粘贴：" + text)
        p = await asyncio.create_subprocess_exec("pbcopy", stdin=asyncio.subprocess.PIPE)
        await p.communicate(text.encode("utf-8"))
        return await self._sh("osascript", "-e",
                              'tell application "System Events" to keystroke "v" using command down')
