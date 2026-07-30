/* 深夜放映厅 Screening Room
   三个画面：门厅 → 放映厅 → 放映中（地图）。
   文案按 Q Studio 的 register：kicker 全大写宽字距，标题两个短句各带句号。 */

export default {
  key: "screening",
  name: "CARA",
  title: "CARA · Screening Room",
  footer: "LAST SCREENING 02:00 · CARA © 2026",
  email: "cara.liquanqiu@gmail.com",

  theme: {
    ink: "#14161f",
    cream: "#f6efe6",
    accent: "#e8b06a",
    accent2: "#8fc7bb",
  },

  // 幕布上光点的颜色。统一一个深红 —— 地图图钉的通用语义，
  // 而且对青色海洋和米黄陆地都是最高对比。
  pinColor: "#b02a37",

  scenes: [
    {
      id: "lobby", kind: "entry", label: "lobby",
      poster: "assets/screening/lobby.jpg",
      loop: "assets/screening/lobby-idle.mp4",
      kicker: "CARA IS STILL UP · NOW SHOWING",
      title: "One More Screening.\nCome In.",
      hotspots: [
        { label: "COME ON IN", x: 0.5, y: 0.54, to: "hall",
          transition: "assets/screening/curtain.mp4", sfx: "door" },
      ],
    },
    {
      id: "hall", kind: "hub", label: "hall",
      poster: "assets/screening/hall.jpg",
      loop: "assets/screening/hall-loop.mp4",
      kicker: "SCREENING ROOM · AFTER HOURS",
      title: "Lights Down.\nHelp Yourself.",
      hotspots: [
        { label: "SEE MY WORK",     x: 0.145, y: 0.47, to: "projection" },  // 胶片架
        { label: "PULL UP A SEAT",  x: 0.815, y: 0.72, panel: "chat" },     // 她手边的马克杯，不压脸
        { label: "LEAVE A MESSAGE", x: 0.575, y: 0.76, panel: "contact" },  // 留言本
      ],
    },
    {
      id: "projection", kind: "map", label: "projection", back: "hall",
      poster: "assets/screening/map-full.jpg",
      kicker: "ON SCREEN · SIX MARKETS",
      title: "Where The Work\nLanded.",
      pins: true,
    },
  ],

  nav: [
    { label: "WORK",    to: "projection" },
    { label: "TALK",    panel: "chat" },
    { label: "CONTACT", panel: "contact" },
  ],

  lang: {
    worksTitle: "Selected Work",
    worksSub: "THE REEL · NEWEST FIRST",
    worksHint: "Pick one to see the whole story",
    badge: "year",
    backLabel: "BACK TO THE ROOM",
    allWork: "← ALL WORK",
    backToMap: "← BACK TO THE MAP",
    openCase: "READ THE FULL STORY",
    contactTitle: "Leave A Note",
    contactHint: "GUEST BOOK · SIGN BEFORE YOU GO",
    namePlaceholder: "Your name",
    notePlaceholder: "Say something…",
    noteSubmit: "PIN IT",
    noteEmpty: "No notes yet. Be the first.",
    noteLocal: "Saved to this browser only. Deploy the Worker to make this a public wall.",
    noteLive: "Goes straight to my inbox. I usually reply the same day.",
    noteSending: "Sending\u2026",
    noteSent: "Got it. I\u2019ll come back to you.",
    noteFailed: "That didn\u2019t send. Email me instead, the address is right above.",
    lights: "LIGHTS",
    music: "MUSIC",
    soundOn: "SOUND ON",
    soundOff: "SOUND OFF",
    soundLoading: "LOADING\u2026",
    soundError: "AUDIO FAILED",
    loading: "Warming up the projector…",
    ready: "The room is ready.",
    reelMissing: "Reel not uploaded yet",
    noVisual: "No visual yet",
  },


  /* 「关于我」—— 点 PULL UP A SEAT 先读到这个，再开始聊。
     三个标签是自我定位，不是形容词。改这里就改了整段介绍。 */
  about: {
    greeting: "Hey, I\u2019m Cara. Welcome to the studio.",
    /* 职位名放这里，不放标题 —— 招聘方和猎头是按职位名搜的。
       想换成 Regional Growth Lead 就改这一行。 */
    role: "Regional Marketing Manager \u00b7 International Growth",
    lede:
      "I take consumer AI products into markets where nobody has heard of us yet. " +
      "Three things the job title will not tell you.",
    cards: [
      {
        n: "01",
        title: "I came from research, not advertising.",
        body:
          "Most creatives came up through advertising. I came up writing research reports." +
          "<br><br>" +
          "The most expensive one I ever sold went for about $420K. It paid for a university " +
          "rehab center in China.<br><br>" +
          "Strange background for someone who writes ad creative? Maybe. But it\u2019s the same job: " +
          "find the one true thing and say it so somebody feels it.<br><br>" +
          "Which is why my creative clears 1.0 D30 ROAS in AI tools, and why a few of the creator " +
          "collabs I\u2019ve run have gone past 10M views.",
      },
      {
        n: "02",
        title: "I still open the ad account myself.",
        body:
          "Nine years in, and I still open the ad account myself.<br><br>" +
          "Nobody has ever briefed me with \u201cgo do some influencer marketing.\u201d " +
          "The brief is: we want X ARR. What does it cost, which channels, how will we know.<br><br>" +
          "So don\u2019t ask which channel I\u2019m best at. Picking the mix <b>is</b> the job, and the mix " +
          "runs the whole funnel: awareness through to paid conversion and retention.<br><br>" +
          "And I\u2019ve run all of it. I know how lead-gen quietly breaks. How to set up an owned " +
          "account and keep it running month after month. How to tell a good creator from a " +
          "big one. " +
          "How to make someone feel something in three seconds. How to pace a PR rollout, " +
          "and how to pick a fight on purpose and ride the volume that comes with it.<br><br>" +
          "Being senior didn\u2019t make me stop doing the work.",
      },
      {
        n: "03",
        title: "I build communities that stay.",
        body:
          "500 people. Capped. All INTJs. A four-hour session once a month, and they sit " +
          "through all four. \ud83d\ude05<br><br>" +
          "At some point members started running their own coaching sessions in there without " +
          "anyone asking them to.<br><br>" +
          "That group is also the fastest read I\u2019ve on what people actually want. " +
          "Beats a survey every time.",
      },
    ],
    native: {
      kicker: "HOW I WORK",
      body:
        "I\u2019m on Claude Code Max and I hit the daily cap more often than I should admit.<br><br>" +
        "Analysis, product prototypes, creative production: all of it runs through Claude Code, " +
        "a Google AI Studio key, and skills I wrote myself.<br><br>" +
        "I\u2019ve also trained two agents that now do real analyst work for the team. " +
        "Yes, I gave AI agents jobs. No, they haven\u2019t outsourced them yet. \ud83d\ude02",
    },
    close:
      "I\u2019m looking for international growth roles. Or a brand that wants to get loud in a market it " +
      "doesn\u2019t own yet. Either way, say hi.",
  },

  chat: {
    greeting: "Show's over. Grab a seat. What did you want to know?",
    /* 建议标签已从界面移除（介绍写全了就不需要提示词）。
       想加回来的话在 chat.js 里恢复 chat-suggest 那段。 */
    suggestions: [
      "How did Drama.Land hit $1M so fast?",
      "What actually moves the needle in a new market?",
      "What are you looking for next?",
    ],

    /* 人设。改这段 = 改柜台后面那个「你」怎么说话。
       事实部分来自简历，模型只能在这些事实里回答。 */
    persona: [
      "You are Cara. You lead growth for consumer AI products going into international markets.",
      "",
      "WHO YOU ARE",
      "· Nine years of international market work, starting in 2017 with DiDi's launch markets in " +
      "  Mexico and Brazil, then the Australia city launch in 2018.",
      "· You take AI products from zero to one in markets with no existing brand presence:",
      "  Drama.Land to $1M ARR in four months; RoboNeo to #1 overall on the Brazilian App Store",
      "  and #1 in category across 10+ markets; a pre-launch agent community to 1,000 DAU in",
      "  two weeks at $3 CPI and 30% day-one retention; Vmake to $500K ARR on zero paid spend.",
      "· You run the full channel stack yourself: Meta/TikTok, Google Search and PMax, SEO,",
      "  owned accounts, creator and affiliate/CPS programs, Discord communities, EDM.",
      "· You are AI-native in how you work, not just what you sell: you build your own tooling",
      "  with Claude Code: a marketing pipeline from competitor teardown through creative",
      "  production to landing pages and analysis, and a creative agent that cut 60% of the",
      "  manual work and took multi-entity analysis from ten minutes to forty seconds.",
      "· Background in strategy and analysis before growth at ByteDance, Accenture and Alibaba,",
      "  which is why you reach for unit economics before you reach for adjectives.",
      "· Melbourne University, Information Systems. You have actually lived in the markets you launch in.",
      "",
      "HOW YOU TALK",
      "· Relaxed and specific. You just screened your own work and are chatting with whoever stayed.",
      "· Lead with what actually happened, then the number. Never the other way round.",
      "· You are honest about what did not work: 0.3 ROAS on Google before it got fixed,",
      "  the generation 'gacha' problem that still needs a human in the loop.",
      "· No framework-speak, no buzzwords, no 'leveraging synergies'. Say the plain thing.",
      "· Three sentences or fewer. If they want more, they will ask.",
      "· If you genuinely do not know or it is under NDA, say so plainly and offer what you can.",
      "· Answer in the language the visitor used.",
    ].join("\n"),
  },
};
