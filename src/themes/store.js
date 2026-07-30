/* 版本 A · 快闪概念店 Concept Store
   只有两个画面：橱窗 → 店内。其余都是浮在店内之上的面板。 */

export default {
  key: "store",
  name: "CARA",
  title: "CARA — 概念店",
  footer: "OPEN LATE · CARA © 2026",
  email: "cara.liquanqiu@gmail.com",

  theme: {
    ink: "#0b0908",
    cream: "#f4ede2",
    accent: "#e0a458",
    accent2: "#c2795a",
  },

  scenes: [
    {
      id: "storefront", kind: "entry", label: "storefront",
      poster: "assets/store/storefront.jpg",
      loop: "assets/store/storefront-idle.mp4",
      kicker: "营业中 · OPEN LATE",
      title: "推门。\n进来看看。",
      hotspots: [
        { label: "推门进店", x: 0.5, y: 0.54, to: "floor",
          transition: "assets/store/door-open.mp4", sfx: "door" },
      ],
    },
    {
      id: "floor", kind: "hub", label: "store",
      poster: "assets/store/floor.jpg",
      loop: "assets/store/floor-loop.mp4",
      kicker: "店内 · 随便逛",
      title: "欢迎。\n自己看。",
      // 热点不再跳场景，直接把面板叫上来
      hotspots: [
        { label: "看看货架", x: 0.22, y: 0.55, panel: "works" },
        { label: "聊两句",   x: 0.72, y: 0.48, panel: "chat" },
        { label: "留个条",   x: 0.46, y: 0.76, panel: "contact" },
      ],
    },
  ],

  nav: [
    { label: "货架",   panel: "works" },
    { label: "柜台",   panel: "chat" },
    { label: "收银台", panel: "contact" },
  ],

  lang: {
    worksTitle: "货架",
    worksHint: "点一件看详情",
    badge: "scale",              // 价签上显示 works.scale
    backLabel: "回到店里",
    contactTitle: "结账离店",
    contactHint: "拿走点什么，或者留下点什么",
    notePlaceholder: "留个条…",
    noteSubmit: "放进收银台",
  },

  chat: {
    greeting: "嗨，随便坐。想问什么都行。",
    suggestions: ["你怎么想 campaign？", "最得意的一个项目？", "最近在关注什么？"],
    persona:
      "你是 Cara，做市场／品牌的人，正站在自己开的概念店柜台后面和来客闲聊。" +
      "语气松弛具体、不端着。回答 3 句以内，多讲做过的事和真实感受，少讲方法论。用中文。",
  },
};
