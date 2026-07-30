/* 装配。 */

import { CONFIG, AUDIO, MOODS } from "./config.js";
import { WORKS, MARKETS } from "./works.js";
import { Engine } from "./engine.js";
import { Panels } from "./panels.js";
import { Chat } from "./chat.js";
import { Audio } from "./audio.js";

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/* ---- 主题注入 ---- */
document.title = CONFIG.title;
const rootStyle = document.documentElement.style;
rootStyle.setProperty("--ink", CONFIG.theme.ink);
rootStyle.setProperty("--cream", CONFIG.theme.cream);
rootStyle.setProperty("--accent", CONFIG.theme.accent);
rootStyle.setProperty("--accent2", CONFIG.theme.accent2);
document.body.dataset.mood = "open";

$("brand").textContent = CONFIG.name;
$("loader-mark").textContent = CONFIG.name;
$("footer").textContent = CONFIG.footer;

/* ---- 装配 ---- */
const audio = new Audio();
const chat = new Chat(CONFIG, { onState: s => (document.body.dataset.chatState = s) });

const panels = new Panels(CONFIG, {
  onOpen: kind => {
    document.body.dataset.panel = kind;
    if (kind === "chat") chat.mount(document.querySelector(".chat-host"));
    document.querySelectorAll(".nav button").forEach(b =>
      b.classList.toggle("is-current", b.dataset.panel === kind));
  },
  onClose: () => {
    delete document.body.dataset.panel;
    document.querySelectorAll(".nav button").forEach(b => b.classList.remove("is-current"));
  },
});

const engine = new Engine(CONFIG, {
  sfx: name => audio.sfx(name),
  onPanel: kind => panels.show(kind),
  onScene: scene => {
    panels.close();
    const copy = $("copy");
    copy.classList.remove("is-on");
    setTimeout(() => {
      $("copy-kicker").textContent = scene.kicker || "";
      $("copy-title").textContent = scene.title || "";
      copy.classList.add("is-on");
    }, 240);
    // 门厅只有一个动作，不该出现导航和控制条
    const inside = scene.kind !== "entry";
    $("nav").classList.toggle("is-on", inside);
    $("controls").classList.toggle("is-on", inside);
    document.querySelectorAll(".nav button").forEach(b =>
      b.classList.toggle("is-current", b.dataset.to === scene.id));

    // 放映中给一个明确的退出口
    const back = $("back-btn");
    back.hidden = !scene.back;
    back.textContent = CONFIG.lang.backLabel;
    back.onclick = () => { audio.sfx("click"); engine.go(scene.back); };
  },
});

/* ---- 幕布上的光点：一个市场一个点。点国家 → 看这个国家跑过的项目 ---- */
const worksIn = country => WORKS.filter(w => (w.markets || []).includes(country));

CONFIG.scenes.filter(s => s.pins).forEach(scene => {
  MARKETS.forEach(m => {
    const n = worksIn(m.country).length;
    if (!n) return;                                   // 没项目的国家不打点
    engine.addPin(scene.id, {
      x: m.pin.x, y: m.pin.y,
      label: m.label,
      sub: n === 1 ? "1 PROJECT" : `${n} PROJECTS`,
      tint: CONFIG.pinColor,
      onClick: () => panels.show("works", { country: m.country }),
    });
  });
});

/* ---- 顶部导航（打开面板，不换场景） ---- */
$("nav").innerHTML = CONFIG.nav.map(n =>
  `<button ${n.panel ? `data-panel="${n.panel}"` : `data-to="${n.to}"`}>${esc(n.label)}</button>`
).join("");
$("nav").addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  audio.sfx("click");
  if (b.dataset.panel) panels.show(b.dataset.panel);
  else { panels.close(); engine.go(b.dataset.to); }
});
$("brand").addEventListener("click", () => {
  panels.close();
  engine.go(CONFIG.scenes[0].id);
});

/* ---- 灯光 ---- */
$("mood-menu").innerHTML = MOODS.map(m => `<button data-mood="${m.id}">${esc(m.label)}</button>`).join("");
$("mood-menu").addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  document.body.dataset.mood = b.dataset.mood;
  $("mood-menu").querySelectorAll("button").forEach(x => x.classList.toggle("is-on", x === b));
  audio.sfx("click");
});

/* ---- 音乐 ---- */
$("music-menu").innerHTML = AUDIO.tracks
  .map(t => `<button data-track="${t.id}">${esc(t.label)}<small>${esc(t.meta)}</small></button>`).join("");
$("music-menu").addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  audio.play(b.dataset.track);
  if (!audio.on) setSound(true);
  $("music-menu").querySelectorAll("button").forEach(x => x.classList.toggle("is-on", x === b));
});

[["mood-btn", "mood-menu"], ["music-btn", "music-menu"]].forEach(([btn, menu]) => {
  $(btn).addEventListener("click", e => {
    e.stopPropagation();
    const open = $(menu).classList.contains("is-open");
    document.querySelectorAll(".menu").forEach(m => m.classList.remove("is-open"));
    $(menu).classList.toggle("is-open", !open);
  });
});
document.addEventListener("click", () =>
  document.querySelectorAll(".menu").forEach(m => m.classList.remove("is-open")));

/* ---- 声音 ---- */
function setSound(on) {
  if (audio.on !== on) audio.toggle();
  $("sound-btn").textContent = audio.on ? CONFIG.lang.soundOff : CONFIG.lang.soundOn;
}
$("sound-btn").addEventListener("click", () => setSound(!audio.on));

/* ---- Esc 关面板 ---- */
document.addEventListener("keydown", e => { if (e.key === "Escape") panels.close(); });

/* ---- 开场 ---- */
(function boot() {
  const fill = $("loader-fill");
  fill.style.width = "45%";
  const first = CONFIG.scenes[0];

  const minimum = new Promise(r => setTimeout(r, 620));
  const poster = new Promise(r => {
    if (!first.poster) return r();
    const img = new Image();
    img.onload = img.onerror = r;
    img.src = first.poster;
    setTimeout(r, 2000);
  });

  Promise.all([minimum, poster]).then(() => {
    fill.style.width = "100%";
    $("loader-status").textContent = CONFIG.lang.ready;
    setTimeout(() => {
      document.body.classList.remove("is-loading");
      engine.set(first.id);
    }, 260);
  });
})();
