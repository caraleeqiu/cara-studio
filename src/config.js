/* 版本切换器。
   ?v=store      → 快闪概念店
   ?v=screening  → 深夜放映厅
   不带参数时用 DEFAULT。 */

import store from "./themes/store.js?v=1785416501";
import screening from "./themes/screening.js?v=1785416501";

const DEFAULT = "screening";
const THEMES = { store, screening };

const requested = new URLSearchParams(location.search).get("v");
export const CONFIG = THEMES[requested] || THEMES[DEFAULT];
export const OTHER = CONFIG.key === "store" ? THEMES.screening : THEMES.store;

/* 对话后端。部署 worker/ 之后把地址填这里，聊天就从兜底切到真模型。
   见 worker/README.md。留空时显示诚实的兜底文案，站点照样跑。 */
export const CHAT_WORKER = "";

/* 留言墙和对话共用同一个 Worker（见 CHAT_WORKER）。
   Worker 里 /notes 端点存公开留言，/chat 端点跑对话。 */

export const AUDIO = {
  tracks: [
    { id: "night", label: "Night Shift", src: "assets/audio/night.m4a", meta: "SLOW · WARM" },
    { id: "neon",  label: "Neon Aisle",  src: "assets/audio/neon.m4a",  meta: "LIGHT · STEADY" },
    { id: "reel",  label: "Reel Room",   src: "assets/audio/reel.m4a",  meta: "COOL · QUIET" },
  ],
  sfx: { click: "assets/audio/click.mp3", door: "assets/audio/door.mp3" },
};

export const MOODS = [
  { id: "open", label: "Lights On" },
  { id: "dim",  label: "Dimmed" },
  { id: "neon", label: "Neon" },
];
