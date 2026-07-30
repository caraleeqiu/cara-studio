/* 柜台 / 散场对话。
   接上 Worker 走流式；没接则用本地兜底，站点照样能演。 */

import { CHAT_WORKER } from "./config.js";

const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* Worker 没配好时的关键词兜底 */
const SCRIPTED = [
  { match: ["work", "project", "campaign", "reel", "made"],
    reply: ["It's all up on the map. ", "Pick a pin and I'll walk you through that one."] },
  { match: ["contact", "hire", "reach", "email", "work with"],
    reply: ["Leave a note — fastest way to reach me. ", "Email works too, I usually reply same day."] },
  { match: ["who are you", "about you", "yourself", "your name"],
    reply: ["Marketing person, mostly brand and campaign work. ", "I built this room myself — half portfolio, half toy."] },
];
/* Worker 没接上时的诚实兜底 —— 装作答不上来比说清楚更糟 */
const FALLBACK = [
  "The live chat is not wired up on this build yet. ",
  "Everything I would tell you is in the write-ups on the map, or just email me.",
];

export class Chat {
  constructor(config, { onState } = {}) {
    this.config = config;
    this.onState = onState || (() => {});   // 'wait' | 'talk'
    this.history = [];
    this.busy = false;
    this.node = null;
  }

  mount(container) {
    const c = this.config.chat;
    const wrap = el("div", "chat");

    // 先读介绍，再开始聊 —— 陌生人需要先知道你是谁
    const a = this.config.about;
    if (a) {
      const intro = el("div", "about");
      intro.innerHTML =
        `<h2>${esc(a.greeting)}</h2>` +
        (a.role ? `<div class="about-role">${esc(a.role)}</div>` : "") +
        `<p class="about-lede">${esc(a.lede)}</p>` +
        `<div class="about-cards">` +
        a.cards.map(k =>
          `<article><span>${esc(k.n)}</span><h3>${esc(k.title)}</h3><p>${k.body}</p></article>`
        ).join("") +
        `</div>` +
        (a.native ? `<div class="about-native"><span>${esc(a.native.kicker)}</span>` +
                    `<p>${a.native.body}</p></div>` : "") +
        `<p class="about-close">${esc(a.close)}</p>`;
      wrap.append(intro);
    }

    this.log = el("div", "chat-log");

    const form = el("form", "chat-input");
    form.innerHTML = `<input placeholder="Say something…" maxlength="200" autocomplete="off"><button type="submit">SEND</button>`;
    form.addEventListener("submit", e => {
      e.preventDefault();
      const input = form.querySelector("input");
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      this.send(text);
    });

    wrap.append(this.log, form);
    container.innerHTML = "";
    container.append(wrap);
    this.node = wrap;

  }

  bubble(cls, text) {
    const b = el("div", `bubble ${cls}`, esc(text));
    this.log.append(b);
    this.log.scrollIntoView?.({ block: "end" });
    return b;
  }

  typing() {
    const b = el("div", "bubble you typing", "<i></i><i></i><i></i>");
    this.log.append(b);
    return b;
  }

  /* 一句一个气泡，逐条吐 —— 比整段甩出来像人 */
  async say(text) {
    this.onState("talk");
    // 中英文都按句子切；英文句号后要跟空格或结尾，免得把 "3.8" 切开
    const parts = String(text)
      .split(/(?<=[。！？\n])|(?<=[.!?])(?=\s|$)/)
      .map(s => s.trim())
      .filter(Boolean);
    for (const p of parts) {
      this.bubble("you", p);
      await sleep(Math.min(1100, 260 + p.length * 42));
    }
    this.onState("wait");
  }

  async send(text) {
    if (this.busy) return;
    this.busy = true;
    this.bubble("me", text);
    const dots = this.typing();

    try {
      const answer = CHAT_WORKER
        ? await this.ask(text)
        : (await sleep(700), this.scripted(text));
      dots.remove();
      await this.say(answer);
      this.history.push({ role: "user", content: text }, { role: "assistant", content: answer });
      this.history = this.history.slice(-12);
    } catch {
      dots.remove();
      await this.say("Lost my train of thought there. Ask me again?");
    } finally {
      this.busy = false;
    }
  }

  scripted(text) {
    const q = text.toLowerCase();
    const hit = SCRIPTED.find(s => s.match.some(m => q.includes(m)));
    return (hit ? hit.reply : FALLBACK).join("");
  }

  async ask(text) {
    const resp = await fetch(CHAT_WORKER.replace(/\/$/, "") + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        persona: this.config.chat.persona,
        messages: [...this.history, { role: "user", content: text }],
      }),
    });
    if (!resp.ok || !resp.body) throw new Error("chat unavailable");

    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = "", out = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        try {
          const j = JSON.parse(payload);
          out += j.delta || "";
        } catch { /* 忽略半截 chunk */ }
      }
    }
    return out || "Hm — not sure how to put that one.";
  }
}
