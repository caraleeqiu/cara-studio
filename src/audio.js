/* 声音。素材缺失时静默降级，不报错。 */

import { AUDIO } from "./config.js";

export class Audio {
  constructor() {
    this.on = false;
    this.track = null;
    this.bgm = new window.Audio();
    this.bgm.loop = true;
    this.bgm.volume = 0;
    this.sfxCache = new Map();
  }

  toggle() {
    this.on = !this.on;
    if (this.on) {
      if (!this.track) this.play(AUDIO.tracks[0].id);
      else this.fade(0.32);
    } else {
      this.fade(0);
    }
    return this.on;
  }

  play(id) {
    const t = AUDIO.tracks.find(x => x.id === id);
    if (!t) return;
    this.track = id;
    this.bgm.src = t.src;
    this.bgm.play().then(() => this.fade(this.on ? 0.32 : 0)).catch(() => {});
  }

  fade(target) {
    clearInterval(this._fade);
    const step = (target - this.bgm.volume) / 24;
    this._fade = setInterval(() => {
      const next = this.bgm.volume + step;
      if ((step > 0 && next >= target) || (step < 0 && next <= target) || !step) {
        this.bgm.volume = Math.max(0, Math.min(1, target));
        clearInterval(this._fade);
        if (!target) this.bgm.pause();
        return;
      }
      this.bgm.volume = Math.max(0, Math.min(1, next));
    }, 40);
  }

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
