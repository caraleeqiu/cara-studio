"""菜单栏小图标：模拟交付形态。没在 Mac 上跑过，逻辑简单，出问题贴报错。

  pip install rumps
  python tools/menubar.py

要求调度器已经 --serve 在跑。
"""

import urllib.request

import rumps

INBOX = "http://127.0.0.1:8765"


def post(path, body=""):
    req = urllib.request.Request(INBOX + path, data=body.encode("utf-8"), method="POST")
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")


class App(rumps.App):
    def __init__(self):
        super().__init__("◎", quit_button="退出")
        self.menu = ["说一句", "进度", None, "发", "算了"]

    @rumps.clicked("说一句")
    def say(self, _):
        # 输入框里按 Mac 自带听写快捷键（默认按两下 Fn）就能说
        w = rumps.Window(message="说吧（按两下 Fn 用听写）", title="派活", ok="派", cancel="算了")
        r = w.run()
        if r.clicked and r.text.strip():
            rumps.notification("派活", "", post("/say", r.text.strip()))

    @rumps.clicked("进度")
    def status(self, _):
        rumps.alert("进度", urllib.request.urlopen(INBOX + "/status", timeout=5).read().decode("utf-8"))

    @rumps.clicked("发")
    def confirm(self, _):
        rumps.notification("派活", "", post("/say", "发"))

    @rumps.clicked("算了")
    def cancel(self, _):
        rumps.notification("派活", "", post("/say", "算了"))


if __name__ == "__main__":
    App().run()
