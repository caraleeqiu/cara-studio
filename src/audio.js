/* 声音。
 *
 * 两条原则：
 *   1. 失败不能静默 —— 点了按钮没反应，用户分不清是坏了还是在加载
 *   2. 等能播了再 play() —— 直接对刚设 src 的元素调 play()，浏览器会 reject
 */

import { AUDIO } from "./config.js";

const FULL = 0.32;          // 背景音乐的目标音量，压得低一点

export class Audio {
  constructor({ onState } = {}) {
    this.on = false;
    this.track = null;
    this.onState = onState || (() => {});   // 'off' | 'loading' | 'playing' | 'error'
    this.bgm = new window.Audio();
    this.bgm.loop = true;
    this.bgm.preload = "none";
    this.bgm.volume = 0;
    this.sfxCache = new Map();

    // 播放中被打断（切后台、设备变化）也要让界面知道
    this.bgm.addEventListener("pause", () => {
      if (this.on && this.bgm.volume > 0) this.onState("off");
    });
  }

  async toggle() {
    if (this.on) {
      this.on = false;
      this.fade(0);
      this.onState("off");
      return false;
    }
    this.on = true;
    await this.play(this.track || AUDIO.tracks[0].id);
    return this.on;
  }

  /* 等到真的能播再 play()。src 刚设好就 play() 会被浏览器拒掉。 */
  async play(id) {
    const t = AUDIO.tracks.find(x => x.id === id);
    if (!t) return;

    const switching = this.track !== id;
    this.track = id;
    this.on = true;

    if (switching) {
      this.bgm.pause();
      this.bgm.volume = 0;
      this.bgm.src = t.src;
    }

    this.onState("loading");
    try {
      if (this.bgm.readyState < 3) {           // HAVE_FUTURE_DATA
        this.bgm.load();
        await new Promise((resolve, reject) => {
          const ok = () => { cleanup(); resolve(); };
          const bad = () => { cleanup(); reject(new Error("cannot load " + t.src)); };
          const cleanup = () => {
            this.bgm.removeEventListener("canplay", ok);
            this.bgm.removeEventListener("error", bad);
            clearTimeout(timer);
          };
          const timer = setTimeout(bad, 15000);
          this.bgm.addEventListener("canplay", ok, { once: true });
          this.bgm.addEventListener("error", bad, { once: true });
        });
      }
      await this.bgm.play();
      this.fade(FULL);
      this.onState("playing");
    } catch (err) {
      // 不吞掉 —— 界面要能显示出问题
      this.on = false;
      this.onState("error");
      console.warn("[audio]", err.message);
    }
  }

  fade(target) {
    clearInterval(this._fade);
    const from = this.bgm.volume;
    const steps = 20;
    const step = (target - from) / steps;
    if (!step) {
      this.bgm.volume = target;
      if (!target) this.bgm.pause();
      return;
    }
    let i = 0;
    this._fade = setInterval(() => {
      i += 1;
      const v = i >= steps ? target : from + step * i;
      this.bgm.volume = Math.max(0, Math.min(1, v));
      if (i >= steps) {
        clearInterval(this._fade);
        if (!target) this.bgm.pause();
      }
    }, 40);
  }

  /* 音效缺文件是常态（没做音效素材），这里静默是对的 ——
     它不是用户主动请求的动作，失败了也不影响任何事。 */
  sfx(name) {
    if (!this.on) return;
    const src = AUDIO.sfx[name];
    if (!src) return;
    let a = this.sfxCache.get(name);
    if (!a) { a = new window.Audio(src); this.sfxCache.set(name, a); }
    a.currentTime = 0;
    a.volume = 0.45;
    a.play().catch(() => {});
  }
}
