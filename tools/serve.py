#!/usr/bin/env python3
"""本地开发服务器。和 python -m http.server 的区别：不发缓存头。

浏览器对 ES module 的缓存很激进，改完代码刷新还是跑旧的，
调起来会怀疑人生。这个脚本强制 no-store。

    python3 tools/serve.py          # 默认 8777
    python3 tools/serve.py 9000
"""

import functools, http.server, pathlib, socketserver, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8777


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_response(self, *args, **kwargs):
        # 不让 304 回来，永远给完整内容
        super().send_response(*args, **kwargs)

    def log_message(self, fmt, *args):
        if "404" in (fmt % args):
            sys.stderr.write(f"  404  {args[0] if args else ''}\n")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    handler = functools.partial(NoCache, directory=str(ROOT))
    with Server(("127.0.0.1", PORT), handler) as httpd:
        print(f"→ http://localhost:{PORT}   (no-cache, Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
