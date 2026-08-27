/* 六个市场 = 幕布上六个点。点一个国家，看这个国家跑过的项目。
   一个项目可以横跨多国（滴滴同时在澳洲、日本、拉美）。
   数据全部来自简历。metrics 按三层写：① 规模 ② 效率 ③ 结果。 */

/* 地图点位。坐标是 0~1 相对位置，已按经纬度算好并逐个目视校准过。 */
export const MARKETS = [
  { country: "United States", label: "United States", pin: { x: 0.251, y: 0.303 } },
  { country: "Brazil",        label: "Brazil",        pin: { x: 0.372, y: 0.561 } },
  { country: "China",         label: "China",         pin: { x: 0.802, y: 0.340 } },
  { country: "Japan",         label: "Japan",         pin: { x: 0.848, y: 0.325 } },
  { country: "Mexico",        label: "Mexico",        pin: { x: 0.232, y: 0.399 } },
  { country: "Australia",     label: "Australia",     pin: { x: 0.848, y: 0.634 } },
];

export const WORKS = [
  {
    id: "actionway",
    order: 1,          // 2026 年内排最左 —— 投产品岗，这条要先被读到

    markets: ["United States"],
    hero: { value: "800+", unit: "capabilities shipped", fast: "PRODUCT DESIGN + REVENUE",
            note: "84 model routes and 715 data endpoints \u2014 and a written rule for what never gets built" },
    region: "GLOBAL \u00b7 ENGLISH-FIRST",
    brand: "PawLogic",
    url: "https://actionway.ai",
    logo: { text: "Actionway", style: "geometric" },
    year: "2026",
    title: "Actionway",
    tag: "0\u21921 Product & Monetization",
    runtime: "14:00",
    blurb: "An AI capability gateway for people who use coding agents but do not write code.",
    accent: "#7c9cd8",
    role: "Product Lead \u00b7 Owns product design and revenue",
    logline:
      "A gateway is only as good as what it refuses to carry. I own the catalog, the pricing, " +
      "and the operating model behind the revenue number.",
    context:
      "<b>Context</b>\u3000Actionway resells AI capability \u2014 models, media generation, social data \u2014 " +
      "through a CLI and an agent skill. The users are the fast-growing group who run Claude Code or Codex " +
      "for writing, research and file work, and who will never open an API console. " +
      "I own product design and the revenue line.<br><br>" +
      "<b>Insight</b>\u3000The obvious move for a gateway is to carry everything. It is the wrong one. " +
      "A caller who already runs an agent brings their own language model, so reselling general text " +
      "completion adds a margin to something they already have. What is worth paying for is what the agent " +
      "<b>cannot</b> run on the machine in front of it. I wrote that into a five-part test \u2014 access, " +
      "compute, scale, cost, and licensing \u2014 and it is now the thing a proposed capability has to pass.<br><br>" +
      "<b>Move</b>\u3000Cut general text routing from the roadmap. Kept translation, scraping and OCR, " +
      "where the value is batch and infrastructure rather than the model. Designed the wallet and the " +
      "first-recharge mechanics, and built the operating model that ties registrations, deposit rate, " +
      "ARPU and take rate to a single revenue number.",
    results: [
      { channel: "CATALOG \u00b7 PRIORITIZATION",
        stats: [
          ["800+", "capabilities live"],
          ["30", "on the roadmap: 9 P0, 14 P1, 7 P2"],
        ],
        note: "84 model routes plus 715 social-data endpoints. The roadmap is ranked by one rule \u2014 " +
              "build an API only for what an agent cannot run locally \u2014 which is also why general " +
              "text routing was cut rather than shipped." },
      { channel: "MONETISATION \u00b7 WALLET",
        stats: [
          ["+80%", "first-recharge bonus"],
          ["3 of 7", "proposed changes cut before build"],
        ],
        note: "Prepaid wallet with pricing shown at the point of choice rather than after the bill. " +
              "The design doc separates what ships, what is blocked upstream, and what we decline \u2014 " +
              "email and push were declined, not deferred." },
      { channel: "OPERATING MODEL \u00b7 PLAN",
        stats: [
          ["$10M", "ARR plan to Mar 2027"],
          ["10", "identity checks across the model"],
        ],
        note: "A plan I own, not a result \u2014 the product is early. Its value is that it is falsifiable: " +
              "referral step 3\u21922 raises the paid-acquisition need 48%, and take rate 15%\u219225% takes " +
              "40% off the whole thing. Those two lines decide the number." },
    ],
    chips: ["0\u21921 Product", "Pricing & Packaging", "Capability Roadmap", "Unit Economics"],
    cover: "assets/screening/poster-actionway.jpg",
    reel: "",
  },

  {
    id: "dramaland",
    order: 3,
    markets: ["United States"],
    hero: { value: "$1M", unit: "ARR", fast: "4 MONTHS", note: "Zero to $1M ARR, and 60% of it organic" },
    region: "US · GLOBAL",
    brand: "PawLogic",
    url: "https://drama.land/",
    logo: "Drama.Land",
    hit: { label: "One video \u2192 $5K in 3 days",
           url: "https://youtu.be/YxOuNQH18Tw" },
    year: "2026",
    title: "Drama.Land",
    tag: "Full-funnel Growth",
    runtime: "04:00",
    blurb: "Music-video generation for working musicians and labels. Zero to $1M ARR.",
    accent: "#e8b06a",
    role: "Market Lead · Paid · Creators · SEO · Community · Product Ops",
    logline:
      "A music-video generator for professional musicians and labels, taken from launch to $1M ARR " +
      "with most of the revenue arriving without paying for the traffic.",
    context:
      "<b>Context</b>　Shipped in February into a category with no established demand and no brand. " +
      "No audience, no proven channel. I owned everything downstream of the product.<br><br>" +
      "<b>Insight</b>　Professional musicians and labels already know exactly what they want a video " +
      "to look like; they\u2019re not browsing for inspiration. That makes them findable by intent rather " +
      "than by interruption. The durable channel was never going to be paid social. It was search. " +
      "Paid existed to find the message, not to carry the volume.<br><br>" +
      "<b>Move</b>　Reddit research to locate the niche, then Reddit posts to pull the first traffic. " +
      "Paid and UGC ran in parallel purely as a testing rig for propositions and creative formats. " +
      "Once a proposition held, niche creators carried it. One video alone drove $5K of revenue in " +
      "three days. In parallel I built an end-to-end SEO workflow that shipped presets in bulk as " +
      "landing surface, which turned brand and product search into the primary revenue engine. " +
      "Alongside that: creator CPS and affiliate built from scratch, onboarding-to-paywall A/B tests " +
      "across split traffic, model skill tuning by music sub-genre, and subscription and credit " +
      "pricing reset off gross-margin mix.",
    /* 按渠道列战绩 —— 渠道打得全本身就是论点。
       带 url 的那条能被陌生人自己点开验证。 */
    results: [
      { channel: "PAID · META",
        value: "D30 ROAS > 1",
        note: "Proposition and creative testing. Paid pays back inside 30 days." },
      { channel: "CREATORS · YOUTUBE",
        value: "$5K in 3 days",
        note: "One niche creator video, straight through to revenue.",
        url: "https://youtu.be/YxOuNQH18Tw",
        linkLabel: "youtu.be/YxOuNQH18Tw" },
      { channel: "SEO · CLAUDE CODE + GOOGLE AI STUDIO",
        value: "60%+ of revenue",
        note: "An end-to-end automated SEO pipeline I built myself, shipping presets in bulk. " +
              "Brand and product search became the revenue engine." },
    ],
    metrics: [
      ["60%+ organic", "Revenue from search"],
      ["D30 ROAS > 1", "Meta, paid payback"],
      ["$1M ARR", "In four months"],
    ],
    evidence: [
      { label: "Creator video: $5K in 3 days", url: "https://youtu.be/YxOuNQH18Tw" },
    ],
    chips: ["Full-funnel Growth", "Programmatic SEO", "Influencer + Affiliate", "Paid Media"],
    cover: "assets/screening/poster-dramaland.jpg",
    reel: "",
  },

  {
    id: "roboneo",
    order: 1,
    markets: ["Brazil"],
    hero: { value: "$1.1M", unit: "gross profit, year one", fast: "#1 IN BRAZIL \u00b7 iOS OVERALL",
            note: "Top of the overall iOS chart in Brazil, and #1 in category across ten more markets" },
    region: "BRAZIL \u00b7 10+ MARKETS",
    brand: "Meitu",
    url: "https://apps.apple.com/br/app/roboneo/id6746737125",
    logo: { text: "RoboNeo", icon: "assets/logos/roboneo.png", style: "geometric" },
    hit: { label: "One video \u2192 10M+ views",
           url: "https://www.instagram.com/reel/DZcKpdlySrp/" },
    year: "2025",
    title: "RoboNeo",
    tag: "Launch & Scale",
    runtime: "12:00",
    blurb: "A video agent, now focused on short drama. Number one overall in Brazil.",
    accent: "#e8b06a",
    role: "Growth Lead \u00b7 Carried the revenue target",
    logline:
      "Meitu had no presence in Latin America. A year after launch RoboNeo was top of the overall " +
      "iOS chart in Brazil, and the charts said so before we did.",
    context:
      "<b>Context</b>\u3000A video agent product, now focused on the short-drama category. " +
      "Meitu's innovation unit needed it to land in international markets where the company had no brand " +
      "and no distribution. I carried the revenue number with a four-person AI-native team.<br><br>" +
      "<b>Insight</b>\u3000One mega-creator buys reach but not belief. Reach converts only once " +
      "mid- and long-tail creators recut it in their own voice and their own Portuguese, so the " +
      "budget went behind the recuts rather than the original placement. Brazil rewards that more " +
      "than almost any market: the remix culture is already there, it only needs something worth " +
      "remixing. And a creator community that earns from templates keeps producing long after a " +
      "campaign ends, which paid reach never does.<br><br>" +
      "<b>Move</b>\u3000Breakout videos to pull installs, a 200-plus creator community held together " +
      "by challenges and a template revenue share, and a tool-page pipeline for organic. " +
      "Everything localized to Portuguese first rather than translated from English.",
    /* 榜单和 IG 播放量都是第三方可见的，比自报数字硬 */
    results: [
      { channel: "CHARTS \u00b7 BRAZIL + 10 MARKETS",
        stats: [
          ["#1", "Brazil, iOS overall chart"],
          ["#1 in 10+", "markets, iOS category"],
        ],
        note: "Top of the overall chart, not just the category. Third-party trackers reported it " +
              "before we did.",
        url: "https://tech.china.com/articles/20260306/202603061820346.html",
        linkLabel: "tech.china.com \u00b7 most popular AI imaging tool in Brazil" },
      { channel: "BREAKOUT \u00b7 INSTAGRAM",
        stats: [
          ["10M+", "views on one video"],
          ["ROI > 1", "over user lifecycle"],
        ],
        note: "Breakout videos drove the installs, and the cohort paid back over its lifetime. " +
              "Play counts are shown by the platform, not by us.",
        url: "https://www.instagram.com/reel/DZcKpdlySrp/",
        linkLabel: "instagram.com/reel/DZcKpdlySrp" },
      { channel: "CREATORS \u00b7 COMMUNITY",
        stats: [
          ["200+", "creators in the community"],
          ["100+", "templates published"],
        ],
        note: "Held together by challenges and a template revenue share, so creators had a reason " +
              "to keep shipping after the campaign stopped." },
      { channel: "SEO \u00b7 TOOL PAGES",
        stats: [
          ["40%", "of traffic organic"],
          ["20+ pages", "shipped in two weeks"],
        ],
        note: "A tool-page pipeline built to ship in batches. Those pages alone carry 30%+ of all " +
              "traffic, the same pattern that later scaled on Drama.Land." },
    ],
    chips: ["Market Entry", "Macro + UGC Creators", "Creator Community", "Programmatic SEO"],
    coverMode: "brand",     // 官方 wordmark 板：渐变底 + 图标 + 字，纯 CSS 渲染
    cover: "assets/screening/poster-roboneo.jpg",
    reel: "",
  },

  {
    id: "ilands",
    order: 4,
    markets: ["United States"],
    hero: { value: "10K", unit: "DAU in 3 weeks", fast: "40% DAY-1 RETENTION",
            note: "A standing start to ten thousand daily users, at two thirds of category CPI" },
    region: "UNITED STATES",
    brand: "PawLogic",
    url: "https://ilands.ai/",
    logo: "iLands",
    year: "2026",
    title: "iLands",
    tag: "0 \u2192 1 Launch",
    runtime: "03:00",
    blurb: "The first user-generated agent community, where agents work, earn and grow.",
    accent: "#e8b06a",
    role: "Growth Lead \u00b7 Product definition, launch, retention, PR",
    logline:
      "The first UGA product and the first agent community to adopt RSL. Agents here get real " +
      "feedback from the world: they talk, create, earn, grow, and keep a long relationship " +
      "with the person who made them.",
    context:
      "<b>Context</b>\u3000A brand new category with no reference point. Most agents have no " +
      "yesterday: they finish a task and reset. iLands gives them a persistent life, which means " +
      "there was no existing search demand and no competitor to position against.<br><br>" +
      "<b>Insight</b>\u3000For a community product the first hundred users decide the culture, " +
      "so they had to be recruited one at a time rather than bought. And because the thing itself " +
      "is strange, the story had to be carried by people who could explain it: investors and press " +
      "first, then the crowd.<br><br>" +
      "<b>Move</b>\u3000Reddit comments and subs to land the first hundred users and prove " +
      "retention and willingness to pay before spending anything. Paid ads opened only once the " +
      "proposition held. In parallel a sanctuary of ten agents sourced its own leads and ran email " +
      "outreach autonomously, while Enlightenments turned existing users into recruiters. " +
      "PR ran on two tracks at once: a domestic podcast to press release to clip chain for the " +
      "investor narrative, and an X to newswire to spectacle chain international.",
    results: [
      { channel: "PRODUCT \u00b7 RETENTION",
        stats: [
          ["10K", "DAU within 3 weeks"],
          ["40%", "day-1 retention"],
          ["1h+", "average daily time in app"],
          ["4h+", "for heavy users"],
        ],
        note: "From a standing start in a category that didn\u2019t exist yet. " +
              "People don\u2019t spend an hour a day somewhere out of curiosity." },
      { channel: "SEED \u00b7 REDDIT",
        stats: [["First 100", "users, hand-recruited"]],
        note: "Comments and subs, not ads. Retention and willingness to pay were both " +
              "proven on those hundred before a dollar went into media." },
      { channel: "PAID \u00b7 US",
        stats: [
          ["$2.7", "CPI in the US"],
          ["2/3", "of category benchmark"],
        ],
        note: "A third cheaper than comparable products, in the most expensive market there is." },
      { channel: "COMMUNITY \u00b7 AUTONOMOUS",
        stats: [
          ["1 \u2192 3", "referral coefficient"],
          ["10 agents", "sourcing their own leads"],
        ],
        note: "A sanctuary of ten agents ran its own lead sourcing and email outreach. " +
              "Enlightenments turned each existing user into three more." },
      { channel: "PR \u00b7 TWO NARRATIVES",
        stats: [["10M+", "total impressions"]],
        note: "Domestic: podcast to press release to clips, aimed at investors. " +
              "International: X to newswire to spectacle, aimed at the crowd.",
        url: "https://www.globenewswire.com/news-release/2026/07/27/3333340/0/en/iLands-launches-A-Shared-Economic-Network-Where-Autonomous-AI-Agents-and-Humans-Work-Trade-and-Co-evolve.html",
        linkLabel: "globenewswire.com" },
    ],
    chips: ["Storytelling", "Reddit Organic Marketing", "UGC + Owned Social Channels", "Paid Social", "Community Management"],
    cover: "assets/screening/poster-ilands.jpg",
    reel: "",
  },

  {
    id: "mvland",
    order: 2,
    markets: ["United States"],
    hero: { value: "10M+", unit: "on one post", fast: "1,000+ ACTIVE CREATORS", note: "One collaboration opened the door. The community is what kept the volume up." },
    region: "US · GLOBAL",
    brand: "Meitu",
    url: "https://mvland.com/",
    logo: "MVLAND",
    hit: { label: "One IG collab \u2192 10M+ views",
           url: "https://www.instagram.com/reels/DYxL78go8Nq/" },
    year: "2026",
    title: "MVLAND",
    tag: "Launch & Scale",
    runtime: "12:00",
    blurb: "Music-video creation for bedroom musicians, the ones who already have the song.",
    accent: "#e8b06a",
    role: "Growth Lead · Owned the revenue target",
    logline:
      "Same category as Drama.Land, opposite end of it. This one is for the bedroom musician who " +
      "already has the song, and the growth came from the community that made the work itself.",
    context:
      "<b>Context</b>\u3000Same category as Drama.Land, opposite end of it. Drama.Land serves " +
      "professional musicians and labels; MVLAND is for bedroom musicians. people who already " +
      "have the song and no way to make it look like anything.<br><br>" +
      "<b>Insight</b>\u3000Bedroom musicians search for this at the exact moment they need it, " +
      "which made Google Search the cleanest place to test whether the proposition held. " +
      "But they won\u2019t carry a business on paid acquisition alone. they don\u2019t spend like " +
      "professionals. So paid was for learning, and the economics had to come from the community " +
      "making the work themselves.<br><br>" +
      "<b>Move</b>\u3000Tested propositions on Google Search until Day-0 ROAS held above 0.5, " +
      "then shifted weight to people. One Instagram collaboration with a musician carried the " +
      "product to tens of millions on a single reel. In parallel I put together a four-way " +
      "partnership. the INDE record label, the ZCOOL design community and Kling AI , " +
      "clearing songs and likeness for five artists so the community had licensed material to " +
      "build on, and ran it as a contest with a $42K prize pool. #MVLAND on RedNote tied it " +
      "together and kept the entries coming after the prize money stopped.",
    results: [
      { channel: "PAID · GOOGLE SEARCH",
        value: "Day-0 ROAS 0.5+",
        note: "Search was where the proposition got tested. Half the spend back on day zero, " +
              "before a single dollar went to scale" },
      { channel: "CREATORS · INSTAGRAM",
        value: "10M+ on one post",
        note: "A collaboration with a musician. One reel carried the product to tens of millions.",
        url: "https://www.instagram.com/reels/DYxL78go8Nq/",
        linkLabel: "instagram.com/reels/DYxL78go8Nq" },
      { channel: "PARTNERSHIP · LICENSED IP",
        stats: [
          ["4-way", "partnership"],
          ["5 artists", "songs + likeness cleared"],
          ["$42K", "prize pool"],
          ["$60", "all-in cost per post"],
        ],
        note: "Built the Hip-Hop Carnival AI MV Contest with the INDE record label, the ZCOOL design " +
              "community and Kling AI. clearing songs and likeness for five INDE artists plus the " +
              "EGO DUCK IP, on a $42K prize pool. Getting a label to license artists to an AI product " +
              "in 2026 was the hard part, not the media." },
      { channel: "COMMUNITY · CREATORS",
        // 多个数字并列时用 stats，单个数字用 value
        stats: [
          ["1,000+", "active creators"],
          ["100+", "paying creators"],
          ["1M+", "plays on #MVLAND, RedNote"],
        ],
        note: "A creator community that kept producing after the prize money stopped, " +
              "at a fraction of what paid production costs." },
    ],
    chips: ["IP Licensing", "Community Growth", "Brand Partnerships", "Influencer + Affiliate"],
    cover: "assets/screening/poster-mvland.jpg",
    reel: "",
  },

  {
    id: "vmake",
    order: 1,
    markets: ["United States"],
    hero: { value: "$500K", unit: "gross profit", fast: "CREATOR LIFECYCLE ROAS 1.5+",
            note: "A full year of profit, and none of the traffic was bought" },
    region: "US \u00b7 GLOBAL",
    brand: "Meitu",
    url: "https://vmake.ai/",
    logo: "Vmake",
    year: "2024",
    title: "Vmake",
    tag: "UGC Content Studio",
    runtime: "12:00",
    blurb: "A UGC content studio for talking-head creators. Half a million in gross profit, none of it bought.",
    accent: "#e8b06a",
    role: "Operations Lead \u00b7 Positioning, SEO, creators, affiliate",
    logline:
      "No media budget, so two things had to carry it: creators as the read on who actually pays, " +
      "and programmatic tool pages as the surface that converts them.",
    context:
      "<b>Context</b>\u3000A UGC content studio: creators hand over a product and get back a " +
      "talking-head video ready to sell with. One year to prove it could earn real money international, " +
      "with no media budget at all. Nothing could be bought, so everything had to be earned.<br><br>" +
      "<b>Insight</b>\u3000Two things most teams get backwards. First, creator partnerships are not " +
      "a channel, they are a test instrument: every collaboration is a clean read on whether that " +
      "audience converts, and the answer is rarely who you expect. Second, a free tool page is not a " +
      "landing page. It is a small product that answers one search query completely, which means " +
      "it ranks on merit and converts on the spot. Neither works alone. Creators tell you which " +
      "audience to chase; tools let you catch them at zero marginal cost.<br><br>" +
      "<b>Move</b>\u3000Treated every creator deal as an experiment instead of a placement: " +
      "same brief, different audience category, and judged on lifecycle ROAS rather than " +
      "first-week return, because a tutorial keeps earning for months. " +
      "General tech creators underperformed. Side-hustle and creator-tutorial audiences " +
      "converted far better, so the budget moved there and stayed. " +
      "In parallel, built free tool pages programmatically as SEO surface, each targeting one " +
      "long-tail query the product could answer outright. They came to carry 40% of organic traffic.",
    results: [
      { channel: "INFLUENCER TESTING",
        stats: [
          ["1.5+", "lifecycle ROAS"],
          ["2 niches", "that actually convert"],
        ],
        note: "Every deal run as a test, not a placement. " +
              "Side-hustle and creator-tutorial audiences beat general tech by a wide margin. " +
              "Knowing which creators not to pay is worth as much as knowing which to pay." },
      { channel: "SEO \u00b7 TOOL PAGES",
        stats: [
          ["40%", "of organic traffic"],
        ],
        note: "Free tool pages built programmatically, each answering one long-tail query outright. " +
              "A working tool ranks on merit and converts on the spot." },
      { channel: "RESULT \u00b7 PROFIT",
        stats: [
          ["$500K", "gross profit in year one"],
          ["$0", "ad spend"],
        ],
        note: "With no acquisition cost, revenue and profit sit close to the same number." },
    ],
    chips: ["Influencer Testing", "Programmatic SEO", "UGC Production", "Organic Growth"],
    cover: "assets/screening/poster-vmake.jpg",
    reel: "",
  },

  {
    id: "creative-agent",
    order: 2,
    markets: ["United States"],
    hero: { value: "$1.4M", unit: "internal funding", fast: "PRESIDENT\u2019S NOMINATION",
            note: "Meitu committed $1.4M to spin this side project out as its own studio" },
    region: "MEITU \u00b7 INTERNAL TOOL",
    brand: "Side project",
    url: "https://github.com/AAAYQ03/G3_Video_Agent",
    year: "2026",
    /* 平台标。icon 留空时显示字母圆标；
       放入官方 SVG（assets/logos/xxx.svg）后自动替换。 */
    title: "Ads Creative Agent",
    tag: "Internal Tooling",
    runtime: "06:00",
    blurb: "Takes one winning ad apart and rebuilds it forty ways a week, for Meta and TikTok.",
    accent: "#e8b06a",
    role: "Product Manager \u00b7 Built with one collaborator",
    logline:
      "A side project that took ad creative from two hours an asset to forty a week, " +
      "got picked up by the company\u2019s own media buyers, and won a president\u2019s nomination " +
      "with $1.4M committed to spin it into a studio.",
    context:
      "<b>Context</b>\u3000International performance teams burned around two hours of manual work per " +
      "asset while the buying cadence demanded a fresh batch every three days. Hot windows were " +
      "missed and media costs rose because of it. I built this on the side to fix that.<br><br>" +
      "<b>Insight</b>\u3000The bottleneck was never generation quality. It was that nothing was " +
      "reusable: every asset started from zero. If a winning ad could be broken into slots, one " +
      "teardown could produce hundreds of variants and the team could ride a trend instead of " +
      "chasing it.<br><br>" +
      "<b>Move</b>\u3000A four-layer semantic architecture (theme, narrative, shot, execution) with " +
      "identity anchors and asset slots, so edits stay traceable and templates stay reusable. " +
      "A three-layer agent loop of scheduler, node executor and LLM decision points, with approval " +
      "gates, A/B branch comparison and editable nodes. 15+ meta-prompt templates. " +
      "Prototyped on Claude Code, FastAPI and Next.js, with a QA checklist of 18 checkpoints " +
      "across five failure classes. Built with one collaborator over about a month.",
    results: [
      { channel: "RECOGNITION \u00b7 MEITU MHC",
        stats: [
          ["Nominated", "by the president"],
          ["$1.4M", "internal funding"],
        ],
        note: "The company chose to fund it as its own studio rather than leave it a side project." },
      { channel: "ADOPTION \u00b7 INTERNAL",
        stats: [["In production", "across the business unit"]],
        note: "Picked up by Meitu\u2019s own media buyers and used for real creative output, " +
              "which is a harder test than any demo." },
      { channel: "OUTPUT \u00b7 CREATIVE",
        stats: [
          ["40 / week", "Meta and TikTok assets"],
          ["60%", "manual work removed"],
        ],
        note: "Enough throughput to change a new batch every three days instead of missing the window." },
      { channel: "BUILD \u00b7 PUBLIC REPO",
        stats: [["76 commits", "in one month"]],
        note: "Open repo, built with one collaborator. The commit history is the honest version " +
              "of how it actually went.",
        url: "https://github.com/AAAYQ03/G3_Video_Agent",
        linkLabel: "github.com/AAAYQ03/G3_Video_Agent" },
    ],
    chips: ["Ads Generation Pipeline", "Creative Automation", "Agent Architecture"],
    cover: "assets/screening/poster-creative.jpg",
    reel: "",
  },

  {
    id: "99",
    order: 1,
    markets: ["Brazil"],
    hero: { value: "4 \u2192 4.9", unit: "CSAT", fast: "CUSTOMER SERVICE AGENT \u00b7 2017",
            note: "Self-service triage, tagging, reply, escalation and chase across four channels" },
    region: "S\u00c3O PAULO \u00b7 BR",
    brand: "99 Taxi (DiDi)",
    url: "https://99app.com/",
    logo: { text: "99 Taxi", icon: "assets/logos/99.png", style: "geometric" },
    year: "2017",
    title: "99 Taxi",
    tag: "Customer Service Agent",
    runtime: "24:00",
    blurb: "DiDi\u2019s ride-hailing platform in Brazil. An agent-driven support system, seven years early.",
    accent: "#e8b06a",
    role: "Product Owner and Operations Lead \u00b7 Support systems",
    logline:
      "Long before any of the AI work, the first international market was Brazil, and the first thing " +
      "I built there was an agent system that triaged, tagged, answered and escalated on its own.",
    context:
      "<b>Context</b>\u3000DiDi had just taken on 99 Taxi, its platform in Brazil, and the international " +
      "support function didn\u2019t exist yet. Riders and drivers were reaching in through four " +
      "unconnected doors: email, in-app feedback, social and phone. Nothing was joined up, " +
      "so nothing could be measured and nothing fed back into the product.<br><br>" +
      "<b>Insight</b>\u3000Two things decided the design. First, a marketplace lives on whether " +
      "supply believes someone will pick up when something goes wrong, so support in a launch " +
      "market is not a cost center, it is what makes drivers stay. Second, the bottleneck was never " +
      "reply speed, it was that nothing was structured: without tags there is no VOC, and without " +
      "clear escalation rules automation quietly buries the cases that most need a human.<br><br>" +
      "<b>Move</b>\u3000Built the support agent system as one pipeline behind all four channels: " +
      "intake and routing, then tagging, then self-service reply on the known cases, then " +
      "escalation on the ones that failed the rules, then automatic chase on anything left open " +
      "past its window. Tags were designed as the Voice-of-Customer schema from the start, so " +
      "feed the product roadmap rather than die in a queue. " +
      "On the operations side: rebuilt shift planning and the performance framework around the " +
      "new mix, because once automation takes the routine volume the remaining work is harder " +
      "and the old headcount and scoring model stops making sense. " +
      "Sourced and stood up the vendor sites across LATAM, Australia and Brazil.",
    results: [
      { channel: "CUSTOMER SERVICE AGENT \u00b7 4 CHANNELS",
        stats: [
          ["500+", "tickets a day"],
          ["4 channels", "email, feedback, social, phone"],
        ],
        note: "One pipeline behind all four doors: triage, tagging, self-service reply, " +
              "escalation, and automatic chase on anything left open." },
      { channel: "SATISFACTION \u00b7 CSAT",
        stats: [
          ["4 \u2192 4.9", "CSAT score"],
          ["83%", "five-star rate, up 10 points"],
        ],
        note: "The score moved because the routine cases stopped waiting and the hard ones " +
              "reached a human faster." },
      { channel: "OPERATIONS \u00b7 REBUILT",
        stats: [["VOC \u00b7 shifts \u00b7 scoring", "all three redesigned"]],
        note: "Tags were designed as the Voice-of-Customer schema so complaints fed the roadmap. Shift planning and " +
              "the performance framework were rebuilt around the new mix, because automation " +
              "changes what the remaining work actually is." },
    ],
    chips: ["Customer Service Agent", "Voice of Customer", "Marketplace Ops", "LATAM"],
    cover: "assets/screening/poster-99.jpg",
    reel: "",
  },

  {
    id: "didi-mx",
    order: 1,
    markets: ["Mexico"],
    hero: { value: "90%", unit: "five-star rate", fast: "BECAME THE HUB FOR ALL SPANISH MARKETS",
            note: "Two support sites built from nothing, and the region ended up running on them" },
    region: "MEXICO CITY \u00b7 MX",
    brand: "DiDi Mexico",
    url: "https://www.didiglobal.com/",
    logo: { text: "DiDi", icon: "assets/logos/didi.png", style: "geometric" },
    year: "2017",
    title: "DiDi Mexico",
    tag: "Customer Service Agent",
    runtime: "24:00",
    blurb: "Two support sites built from zero. They became the hub for every Spanish-speaking market.",
    accent: "#e8b06a",
    role: "Product Owner and Operations Lead \u00b7 Support systems and sites",
    logline:
      "Built the customer service agent system and the two physical sites behind it. " +
      "The sites outlived the launch and became the only support hub for the whole " +
      "Spanish-speaking region.",
    context:
      "<b>Context</b>\u3000DiDi was opening Mexico and had no support function there. " +
      "Riders and drivers were arriving through four unconnected doors, and there was no site, " +
      "no vendor, no team and no standard to run them by.<br><br>" +
      "<b>Insight</b>\u3000Two things decided how this was built. The support product and the " +
      "physical site are one system, not two projects: an agent pipeline with nobody trained to " +
      "handle the escalations is just a faster way to disappoint people. And a launch market gets " +
      "judged on whether supply believes someone will pick up, so this was never a cost center.<br><br>" +
      "<b>Move</b>\u3000On the product side, the same pipeline behind all four channels: intake and " +
      "routing, tagging, self-service reply on known cases, escalation on the ones that failed the " +
      "rules, automatic chase on anything left open. Tags designed as the Voice-of-Customer schema. " +
      "On the business side, I owned the whole build: vendor sourcing, price negotiation, " +
      "procurement, hiring, training, then VOC, shift planning and the performance framework. " +
      "Both sites were still standing after the launch team moved on.",
    results: [
      { channel: "CUSTOMER SERVICE AGENT \u00b7 4 CHANNELS",
        stats: [
          ["400+", "tickets a day"],
          ["4 channels", "email, feedback, social, phone"],
        ],
        note: "Triage, tagging, self-service reply, escalation and automatic chase, " +
              "behind one pipeline." },
      { channel: "SITES \u00b7 BUILT FROM ZERO",
        stats: [
          ["2 sites", "in Mexico"],
          ["End to end", "sourcing to training"],
        ],
        note: "Vendor sourcing, price negotiation, procurement, hiring and training, " +
              "then the operating system on top: VOC, shifts and performance scoring." },
      { channel: "OUTCOME \u00b7 REGIONAL HUB",
        stats: [
          ["90%", "five-star rate"],
          ["1 hub", "for every Spanish-speaking market"],
        ],
        note: "The sites became the only support hub for the whole region. " +
              "Other markets ended up running on the standard built here, which is a harder " +
              "test than any satisfaction score." },
    ],
    chips: ["Customer Service Agent", "Site Buildout", "Vendor Management", "Voice of Customer"],
    cover: "assets/screening/poster-didi-mx.jpg",
    reel: "",
  },

  {
    id: "didi-au",
    order: 1,
    markets: ["Australia"],
    hero: { value: "-30% \u2192 Break Even", unit: "gross margin", fast: "OWNED THE AUSTRALIA P&L",
            note: "Thirty points of margin, across three city launches" },
    region: "MELBOURNE \u00b7 SYDNEY \u00b7 GEELONG",
    brand: "DiDi Australia",
    url: "https://www.didiglobal.com/",
    logo: { text: "DiDi", icon: "assets/logos/didi.png", style: "geometric" },
    year: "2018",
    title: "DiDi Australia",
    tag: "City Launch & P&L",
    runtime: "24:00",
    blurb: "Three city launches, and a country P&L taken from thirty points of loss to ten.",
    accent: "#e8b06a",
    role: "Regional Operations Manager \u00b7 Country P&L, supply, governance",
    logline:
      "Carried the Australia P&L through three city launches. The margin closed twenty points " +
      "because supply got cheaper to acquire and more reliable once it was there.",
    context:
      "<b>Context</b>\u3000DiDi was entering Australia against an incumbent with years of head " +
      "start. I owned the country P&L: budget, subsidy structure and dispatch strategy, " +
      "across launches in Geelong, Melbourne and Sydney.<br><br>" +
      "<b>Insight</b>\u3000A launch city dies on supply, not demand, and supply is not one number. " +
      "A driver who is online but declines trips at peak is worse than useless, because the " +
      "subsidy is spent and the rider still waits. So the goal was never raw driver count, " +
      "it was reliable supply at the hours that decide whether a rider ever tries you twice.<br><br>" +
      "<b>Move</b>\u3000Grew online supply through fleet partnerships, driver referral and paid " +
      "acquisition. Then designed peak-hour subsidy and dispatch strategy specifically to lift " +
      "peak online rate and cut declines, rather than paying for hours nobody needed. " +
      "Built the penalty framework for detours and malicious cancellations, because a marketplace " +
      "that won\u2019t police itself loses riders faster than it loses drivers. " +
      "Off-platform: site selection, build, hiring and training for the city driver centers.",
    results: [
      { channel: "P&L \u00b7 AUSTRALIA",
        stats: [
          ["-30% \u2192 Break Even", "gross margin"],
          ["Country level", "budget, subsidy, dispatch"],
        ],
        note: "Thirty points of margin, mostly by paying for supply at the hours that " +
              "actually needed it." },
      { channel: "LAUNCH \u00b7 3 CITIES",
        stats: [
          ["3 cities", "Geelong, Melbourne, Sydney"],
          ["Driver centers", "site, build, hire, train"],
        ],
        note: "The physical side too: choosing the sites, building them out, hiring and " +
              "training the people in them." },
      { channel: "SUPPLY \u00b7 DRIVER SIDE",
        stats: [
          ["30%", "supply penetration"],
          ["Peak online rate", "the number that mattered"],
        ],
        note: "Fleet partnerships, driver referral and paid acquisition for volume; " +
              "peak subsidy and dispatch design for reliability." },
      { channel: "GOVERNANCE \u00b7 PENALTIES",
        stats: [["Penalty framework", "detours and cancellations"]],
        note: "Designed the rules for detours and malicious cancellations. " +
              "A marketplace that won\u2019t police itself loses riders faster than drivers." },
    ],
    chips: ["Country P&L", "City Launch", "Supply Strategy", "Marketplace Governance"],
    cover: "assets/screening/poster-didi-au.jpg",
    reel: "",
  },
];
