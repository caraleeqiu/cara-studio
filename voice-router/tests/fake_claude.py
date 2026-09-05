#!/usr/bin/env python3
"""假的 claude 二进制：模仿 `claude -p ... --output-format json`。

- 回显 prompt 的前面几个字当结果
- 带 --resume 时说明是续会话
- prompt 里有 SLEEP=n 就睡 n 秒，用来测并行
- prompt 里有 FAIL 就返回 is_error
"""
import json
import re
import sys
import time
import uuid

args = sys.argv[1:]
prompt = args[args.index("-p") + 1]
resume = args[args.index("--resume") + 1] if "--resume" in args else None

m = re.search(r"SLEEP=(\d+(?:\.\d+)?)", prompt)
if m:
    time.sleep(float(m.group(1)))

if "FAIL" in prompt:
    print(json.dumps({"is_error": True, "result": "worker 炸了", "session_id": resume or "s-fail"}))
    sys.exit(1)

if resume:
    if prompt.startswith("确认"):
        result = f"[{resume}] 已发送"
    else:
        result = f"[{resume}] 新版本：{prompt[:30]}"
    sid = resume
else:
    sid = "s-" + uuid.uuid4().hex[:6]
    result = f"[{sid}] 做完了：{prompt[:30]}"

print(json.dumps({"result": result, "session_id": sid, "is_error": False}, ensure_ascii=False))
