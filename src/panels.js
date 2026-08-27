/* 浮在场景之上的面板：作品 / 聊天 / 留言。
   面板不换场景 —— 背景永远是同一个放映厅，用户不会迷路。 */

import { WORKS } from "./works.js?v=1787808123";
import { CHAT_WORKER } from "./config.js?v=1787808123";

const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));


/* 平台标：有官方 SVG 就用图，没有就退回字母圆标。
   永远不画仿制 logo —— 画歪的假商标比没有更糟。 */
const platformMarks = list => list.map(p =>
  `<i title="${esc(p.name)}">` +
  (p.icon ? `<img src="${esc(p.icon)}" alt="${esc(p.name)}" onerror="this.remove()">` : "") +
  `<b>${esc(p.mark || p.name[0])}</b></i>`
).join("");


/* 品牌 wordmark：可以是字符串，也可以是 { text, icon, style }。
   style 决定字体调性 —— 各家品牌的字不一样，统一成一种就都不像了。
   图标用官方文件，文字用 CSS 排 —— 永远清晰，改字不用重出图。 */
const brandMark = logo => {
  const l = typeof logo === "string" ? { text: logo } : logo;
  return `<span class="item-logo" data-mark="${esc(l.style || "serif")}">` +
    (l.icon ? `<img src="${esc(l.icon)}" alt="" onerror="this.remove()">` : "") +
    `<b>${esc(l.text)}</b></span>`;
};


/* 留言时间：今天说「today」，其余给日期。绝对时间戳在留言墙上太硬。 */
const fmtDate = iso => {
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const days = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days} days ago`;
  return d.toLocaleDateString("en-GB", { month: "short", year: "numeric" });
};

export class Panels {
  constructor(config, { onOpen, onClose } = {}) {
    this.config = config;
    this.lang = config.lang;
    this.root = document.getElementById("panels");
    this.onOpen = onOpen || (() => {});
    this.onClose = onClose || (() => {});
    this.open = null;

    this.shell = el("div", "panel");
    this.closeBtn = el("button", "panel-close", "✕");
    this.closeBtn.addEventListener("click", () => this.close());
    this.body = el("div", "panel-body");
    this.shell.append(this.closeBtn, this.body);
    this.root.append(this.shell);
  }

  show(kind, arg) {
    if (!kind) return this.close();
    this.open = kind;
    this.body.innerHTML = "";
    this.body.append(this[kind](arg));
    this.body.scrollTop = 0;
    this.shell.classList.add("is-mounted");
    requestAnimationFrame(() => this.shell.classList.add("is-on"));
    this.onOpen(kind);
  }

  close() {
    if (!this.open) return;
    this.open = null;
    this.shell.classList.remove("is-on");
    setTimeout(() => this.shell.classList.remove("is-mounted"), 520);
    this.onClose();
  }

  head(title, sub, hint) {
    return el("div", "panel-head",
      `<h2>${esc(title)}</h2>` +
      (sub ? `<span>${esc(sub)}</span>` : "") +
      (hint ? `<p>${esc(hint)}</p>` : ""));
  }

  /* ---------- 作品：列表 ⇄ 详情，同一个面板内切换 ---------- */
  /* focus = { country } 时只看这个国家；不传时看全部。 */
  works(focus) {
    const country = focus?.country;
    const list = country
      ? WORKS.filter(w => (w.markets || []).includes(country))
      : [...WORKS];

    const wrap = el("div");
    const render = () => {
      wrap.innerHTML = "";
      // 从地图点国家进来的，要有一条明确的路回去。
      // 右上角的 ✕ 用户读不出是「回地图」还是「全关掉」。
      if (country) {
        const back = el("button", "detail-back", this.lang.backToMap);
        back.addEventListener("click", () => this.close());
        wrap.append(back);
      }
      wrap.append(this.head(
        country || this.lang.worksTitle,
        country ? `${list.length === 1 ? "1 PROJECT" : list.length + " PROJECTS"} · ${this.lang.worksSub}`
                : this.lang.worksSub,
        this.lang.worksHint));

      // 按年份分组 —— 时间线本身就是「历史的故事」那条轴
      const byYear = new Map();
      list.sort((a, b) => String(b.year).localeCompare(String(a.year)))
          .forEach(w => {
            if (!byYear.has(w.year)) byYear.set(w.year, []);
            byYear.get(w.year).push(w);
          });

      // 所有年份共用同一个列数 —— 某年只有一个项目时，卡片不该被拉满整行
      // 至少 3 列 —— 某年只有一个项目时，卡片不该被拉成整行宽
      const cols = Math.min(4, Math.max(3, ...[...byYear.values()].map(g => g.length)));

      const timeline = el("div", "timeline");
      byYear.forEach((group, year) => {
        // 同年内按 order 从左到右排；重头戏放最右，作为那一年的落点
        group.sort((a, b) => (a.order || 0) - (b.order || 0));
        const row = el("div", "tl-row");
        row.append(el("div", "tl-year", `<b>${esc(year)}</b><i></i>`));
        const rack = el("div", "rack");
        // 一年之内不换行：列数 = 项目数（最多 4 列，再多才折）
        rack.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
        group.forEach(w => rack.append(makeCard(w)));
        row.append(rack);
        timeline.append(row);
      });
      wrap.append(timeline);
    };

    const makeCard = w => {
        // 电影海报式卡片：文字压在画上，一眼先看到那个数
        const card = el("button", "item");
        card.style.setProperty("--pin", w.accent);
        const art = w.coverMode === "brand"
          ? ""                                    // 品牌板用 CSS 渲染，不需要图片
          : w.cover
            ? `<img src="${esc(w.cover)}" alt="" loading="lazy" onerror="this.remove()">`
            : "";
        const h = w.hero;
        const hero = h
          ? `<div class="item-hero">
               <b>${esc(h.value)}</b><em>${esc(h.unit)}</em>
               ${h.fast ? `<i>${esc(h.fast)}</i>` : ""}
             </div>`
          : "";
        // 爆款单独一行 —— 「我能让东西火」的证据，不该埋在详情里。
        // 箭头用不换行空格粘住最后一个词，免得单独掉到下一行。
        const hit = w.hit
          ? `<a class="item-hit" href="${esc(w.hit.url)}" target="_blank" rel="noopener noreferrer">
               <span>HIT</span><b>${esc(w.hit.label)}&nbsp;↗</b></a>`
          : "";
        const host = w.url ? new URL(w.url).hostname.replace(/^www\./, "") : "";
        card.innerHTML = `
          <div class="item-art" data-cover="${esc(w.coverMode || "photo")}">
            ${art}
            ${w.logo ? brandMark(w.logo) : ""}
            ${w.platforms?.length
              ? `<span class="item-platforms">${platformMarks(w.platforms)}</span>`
              : ""}
          </div>
          <div class="item-scrim">
            ${hero}
            <h3>${esc(w.title)}</h3>
            <p>${esc(w.blurb)}</p>
            ${hit}
            ${w.chips?.length
              ? `<div class="item-tags">${w.chips.map(c => `<i>${esc(c)}</i>`).join("")}</div>`
              : ""}
            <div class="item-meta">
              <span>${esc(w.brand)}</span>
              ${w.url ? `<a class="item-link" href="${esc(w.url)}" target="_blank"
                 rel="noopener noreferrer">${esc(host)}&nbsp;↗</a>` : ""}
            </div>
            <div class="item-cta">${esc(this.lang.openCase)}<i>→</i></div>
          </div>`;
        // 卡片里的链接各走各的，别顺手把详情也打开了
        card.querySelectorAll("a").forEach(a =>
          a.addEventListener("click", e => e.stopPropagation()));
        card.addEventListener("click", () => {
          wrap.innerHTML = "";
          wrap.append(this.detail(w, render));
          this.body.scrollTop = 0;
        });
        return card;
    };

    // 始终先看时间轴 —— 年份本身就是信息，跳过它等于丢掉一条线
    render();
    return wrap;
  }

  detail(w, back) {
    const L = this.lang;
    const wrap = el("div", "detail");

    const backBtn = el("button", "detail-back", back === null ? this.lang.backToMap : this.lang.allWork);
    backBtn.addEventListener("click", back);
    wrap.append(backBtn);

    // 头图 = 封面。片子有了就播片子，没有就放这张剧照。
    const shot = el("div", "detail-shot");
    if (w.reel) {
      shot.innerHTML = `<video src="${esc(w.reel)}" controls playsinline preload="metadata"
        onerror="this.closest('.detail-shot').innerHTML='<div class=&quot;screen-empty&quot;>${esc(L.reelMissing)}</div>'"></video>`;
    } else if (w.coverMode === "brand") {
      shot.dataset.cover = "brand";              // 渐变底 + 居中 wordmark，纯 CSS
    } else if (w.cover) {
      shot.innerHTML = `<img src="${esc(w.cover)}" alt=""
        onerror="this.closest('.detail-shot').innerHTML='<div class=&quot;screen-empty&quot;>${esc(L.noVisual)}</div>'">`;
    } else {
      shot.classList.add("is-empty");          // 没图就收起来，别撑一个 16:9 空框
      shot.innerHTML = `<div class="screen-empty">${esc(L.noVisual)}</div>`;
    }
    if (w.logo) shot.insertAdjacentHTML("beforeend", brandMark(w.logo));
    if (w.platforms?.length) shot.insertAdjacentHTML("beforeend",
      `<span class="item-platforms">${platformMarks(w.platforms)}</span>`);
    wrap.append(shot);

    wrap.append(el("div", null,
      `<div class="detail-kicker">${esc(w.region || w.brand)} · ${esc(w.year)} · ${esc(w.brand)}</div>
       <h2>${esc(w.title)}</h2>`));

    // hero —— 一眼看到的那个数，别埋在正文下面
    if (w.hero) {
      const { value, unit, fast, note } = w.hero;
      wrap.append(el("div", "hero",
        `<b>${esc(value)}</b><em>${esc(unit)}</em>` +
        (fast ? `<i>${esc(fast)}</i>` : "") +
        (note ? `<span>${esc(note)}</span>` : "")));
    }

    wrap.append(el("p", "lede", esc(w.logline || w.blurb)));

    // 标签统一放这里，底部不再重复一遍
    if (w.chips?.length) {
      const chips = el("div", "chips");
      w.chips.forEach(c => chips.append(el("i", null, esc(c))));
      wrap.append(chips);
    }

    // 战绩按渠道列 —— 渠道打得全本身就是论点
    if (w.results?.length) {
      const rows = el("div", "results");
      w.results.forEach(r => {
        const row = el(r.url ? "a" : "div", "result");
        if (r.url) {
          row.href = r.url;
          row.target = "_blank";
          row.rel = "noopener noreferrer";
          row.classList.add("is-linked");
        }
        // stats = 多个数字并列；value = 单个数字
        const valueHTML = r.stats?.length
          ? `<div class="result-stats">${r.stats.map(([v, l]) =>
               `<span><b>${esc(v)}</b><i>${esc(l)}</i></span>`).join("")}</div>`
          : `<b class="result-val">${esc(r.value)}${r.url ? " ↗" : ""}</b>`;
        row.innerHTML =
          `<span class="result-ch">${esc(r.channel)}</span>` +
          valueHTML +
          `<span class="result-note">${esc(r.note)}` +
          (r.linkLabel ? `<u>${esc(r.linkLabel)}</u>` : "") +
          `</span>`;
        rows.append(row);
      });
      wrap.append(rows);
    }

    wrap.append(el("div", "detail-body", w.context));

    // results 已经把数字和证据都讲完了，这里再列一遍就是重复。
    // 只有没写 results 的项目才退回到 metrics。
    if (!w.results?.length) {
      const metrics = el("div", "metrics");
      (w.metrics || []).forEach(([n, label]) =>
        metrics.append(el("div", "metric", `<b>${esc(n)}</b><span>${esc(label)}</span>`)));
      wrap.append(metrics);
    }

    // 证据块同理 —— results 里带 url 的那行已经是可点证据了
    if (!w.results?.length && w.evidence?.length) {
      const ev = el("div", "evidence",
        `<span>PROOF</span>` +
        w.evidence.map(e =>
          `<a href="${esc(e.url)}" target="_blank" rel="noopener noreferrer">${esc(e.label)} ↗</a>`
        ).join(""));
      wrap.append(ev);
    }

    return wrap;
  }

  /* ---------- 留言 ---------- */
  contact() {
    const L = this.lang;
    const wrap = el("div", "contact");
    wrap.append(this.head(L.contactTitle, null, L.contactHint));
    wrap.append(el("div", null,
      `<a class="contact-mail" href="mailto:${esc(this.config.email)}">${esc(this.config.email)}</a>`));

    const form = el("form", "form");
    form.innerHTML = `
      <input name="name" placeholder="${esc(L.namePlaceholder)}" maxlength="24" required>
      <textarea name="text" rows="3" placeholder="${esc(L.notePlaceholder)}" maxlength="300" required></textarea>
      <button type="submit">${esc(L.noteSubmit)}</button>
`;

    const wall = el("div", "wall");
    const KEY = "notes:" + this.config.key;
    const local = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; } };

    const paint = notes => {
      wall.innerHTML = notes.length
        ? notes.map(n =>
            `<div class="note"><b>${esc(n.name)}${n.at ? " · " + esc(fmtDate(n.at)) : ""}</b>${esc(n.text)}</div>`
          ).join("")
        : `<div class="note" style="opacity:.4">${esc(L.noteEmpty)}</div>`;
    };

    /* 有 Worker 就读公开留言墙，没有就退回本地。
       公开可见是留言墙和联系表单的根本区别。 */
    const wallUrl = CHAT_WORKER ? CHAT_WORKER.replace(/\/$/, "") + "/notes" : "";
    const loadWall = async () => {
      if (!wallUrl) return paint(local());
      try {
        const r = await fetch(wallUrl);
        const d = await r.json();
        paint(Array.isArray(d.notes) ? d.notes : local());
      } catch { paint(local()); }
    };

    /* 状态行说实话：没接后端就说明「没人看得到」，
       别让访客以为留言送出去了。 */
    const status = el("p", "form-note");
    status.textContent = wallUrl ? L.noteLive : L.noteLocal;

    form.addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(form);
      const note = { name: fd.get("name").trim(), text: fd.get("text").trim() };
      if (!note.name || !note.text) return;

      // 本地先留一份，界面立刻有反馈
      localStorage.setItem(KEY, JSON.stringify([note, ...local()].slice(0, 30)));
      form.reset();

      if (!wallUrl) { paint(local()); return; }

      const btn = form.querySelector("button");
      btn.disabled = true;
      status.textContent = L.noteSending;
      try {
        const r = await fetch(wallUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(note),
        });
        const d = await r.json();
        if (r.ok && Array.isArray(d.notes)) { paint(d.notes); status.textContent = L.noteSent; }
        else { paint(local()); status.textContent = L.noteFailed; }
      } catch {
        paint(local());
        status.textContent = L.noteFailed;
      } finally {
        btn.disabled = false;
      }
    });

    loadWall();
    form.append(status);
    wrap.append(form, wall);
    return wrap;
  }

  chat() { return el("div", "chat-host"); }   // 由 chat.js 填充
}
