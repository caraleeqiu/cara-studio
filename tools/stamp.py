#!/usr/bin/env python3
"""
给资源 URL 打版本戳。每次改完代码、提交之前跑一次：

    python3 tools/stamp.py

GitHub Pages 发的是 cache-control: max-age=600，而且 index.html 上加 ?r=1
只能刷新 HTML —— styles.css 和 src/*.js 是各自独立缓存的，URL 没变就还是旧的。
结果是同一台手机上有的文件是新的、有的是旧的，测出来的现象没法信。

这里把版本号写进每一个资源 URL：URL 变了，缓存就一定失效。
版本号取自当前时间，只要跑过就一定和上次不同。
"""

import pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent


def version():
    # 用最后一次提交的时间戳，同一份代码反复跑得到同一个值，不会制造无谓的 diff
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return str(int(time.time()))


def stamp(text, patterns, ver):
    """把每个 pattern 匹配到的 URL 换成带 ?v=ver 的版本。已有版本号会被替换掉。"""
    n = 0
    for pat in patterns:
        def sub(m):
            nonlocal n
            n += 1
            return f'{m.group(1)}?v={ver}{m.group(3)}'
        text = re.sub(pat, sub, text)
    return text, n


def main():
    ver = version()
    total = 0

    # index.html：样式表和入口脚本
    idx = ROOT / "index.html"
    src = idx.read_text()
    out, n = stamp(src, [
        r'(href="styles\.css)(\?v=[^"]*)?(")',
        r'(src="src/main\.js)(\?v=[^"]*)?(")',
    ], ver)
    if out != src:
        idx.write_text(out)
    total += n
    print(f"  index.html          {n} 处")

    # 每个模块里的相对 import —— 浏览器按 URL 缓存模块，
    # 只戳入口是没用的，入口里 import 的还是没带版本的旧 URL。
    for f in sorted(ROOT.glob("src/**/*.js")):
        src = f.read_text()
        out, n = stamp(src, [r'(from "\.{1,2}/[^"?]+\.js)(\?v=[^"]*)?(")'], ver)
        if out != src:
            f.write_text(out)
        if n:
            print(f"  {f.relative_to(ROOT).as_posix():20s}{n} 处")
        total += n

    print(f"\n版本 {ver} · 共 {total} 处")


if __name__ == "__main__":
    main()
