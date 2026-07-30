/* 场景引擎：图层构建、懒加载、过场、热点。
   素材缺失时自动降级到程序化占位，不会白屏。 */

const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};

/* 探测素材是否存在，避免为不存在的文件挂一堆 error 监听 */
const probeCache = new Map();
function probe(url) {
  if (!url) return Promise.resolve(false);
  if (!probeCache.has(url)) {
    probeCache.set(
      url,
      fetch(url, { method: "HEAD" }).then(r => r.ok).catch(() => false)
    );
  }
  return probeCache.get(url);
}

export class Engine {
  constructor(config, { onScene, onPanel, sfx } = {}) {
    this.config = config;
    this.scenes = config.scenes;
    this.onScene = onScene || (() => {});
    this.onPanel = onPanel || (() => {});
    this.sfx = sfx || (() => {});
    this.current = null;
    this.nodes = new Map();
    this.stage = document.getElementById("stage");
    this.transition = document.getElementById("transition");
    this.build();

    // 竖屏用 contain（房间完整可见），横屏用 cover（铺满）
    const portrait = window.matchMedia("(max-aspect-ratio: 1/1)");
    const applyFit = () => {
      document.body.dataset.fit = portrait.matches ? "contain" : "cover";
      this.layout();
    };
    // resize 也要重算比例，不能只 layout()：layout() 读的是 body.dataset.fit，
    // 那个值只有 applyFit 会改。只靠 media query 的 change 事件不保险 ——
    // 它不是每个环境都发，漏一次就会横过来还用竖屏的排法。
    portrait.addEventListener("change", applyFit);
    window.addEventListener("resize", applyFit);
    window.addEventListener("orientationchange", applyFit);
    applyFit();
  }

  build() {
    this.scenes.forEach(scene => {
      const node = el("section", "scene");
      node.dataset.scene = scene.id;
      node.style.setProperty("--tint", scene.tint || this.config.theme.accent);

      const media = el("div", "scene-media");
      const fallback = el("div", "scene-fallback");
      fallback.dataset.label = scene.label || scene.id;
      media.append(fallback);

      // poster 静帧
      if (scene.poster) {
        const img = el("img");
        img.alt = "";
        img.dataset.src = scene.poster;
        media.append(img);
        node.__poster = img;
      }

      // 循环视频
      if (scene.loop) {
        const v = el("video");
        Object.assign(v, { muted: true, loop: true, playsInline: true, preload: "none" });
        v.setAttribute("playsinline", "");
        v.dataset.src = scene.loop;
        media.append(v);
        node.__loop = v;
      }

      node.append(media);

      // 热点。坐标记在 dataset 上，实际像素位置由 layout() 按图片矩形算。
      (scene.hotspots || []).forEach(h => {
        const spot = el("button", "hotspot");
        spot.dataset.x = h.x;
        spot.dataset.y = h.y;
        spot.append(el("span", "hotspot-label", h.label), el("span", "hotspot-ring"));
        spot.addEventListener("click", () => {
          this.sfx(h.sfx || "click");
          // 热点要么开面板（不换场景），要么走到另一个画面
          if (h.panel) this.onPanel(h.panel);
          else this.go(h.to, h.transition);
        });
        node.append(spot);
      });

      this.stage.append(node);
      this.nodes.set(scene.id, node);
    });
  }

  /* 在场景上钉一个光点（地图用）。由 main.js 按作品数据调用，
     数量永远等于项目数 —— 不会有点不动的死点。 */
  addPin(sceneId, { x, y, label, sub, tint, onClick }) {
    const node = this.nodes.get(sceneId);
    if (!node) return;
    const pin = el("button", "pin");
    pin.dataset.x = x;
    pin.dataset.y = y;
    if (tint) pin.style.setProperty("--pin", tint);
    pin.innerHTML =
      `<span class="pin-dot"></span>` +
      `<span class="pin-tip"><b>${label}</b>${sub ? `<i>${sub}</i>` : ""}</span>`;
    pin.addEventListener("click", () => { this.sfx("click"); onClick(); });
    node.append(pin);
    this.layout();
  }

  /* 把热点/光点放到图片真正渲染到的那块矩形里。
     图是 16:9，屏幕不是 —— 不这么算，窄屏下热点就会飘到画面外。 */
  layout() {
    // 竖屏：热点脱离画面，收成画面下方的按钮组。
    // 16:9 的房间图 contain 之后只有 ~200px 高，热点钉在上面点不准。
    const stacked = document.body.dataset.fit === "contain";
    document.body.dataset.hotspots = stacked ? "stacked" : "pinned";
    if (stacked) {
      // 光点也一样收成列表。手机上地图受宽度限制只能渲染到 ~209px 高，
      // 四个点全挤在这条里 —— 美国和墨西哥圆心只差 21px，热区却是 44px。
      this.stage.querySelectorAll(".hotspot, .pin").forEach(spot => {
        spot.style.left = "";
        spot.style.top = "";
      });
    }

    this.nodes.forEach(node => {
      const box = node.querySelector(".scene-media");
      const media = node.__poster || node.__loop;
      if (!box) return;

      // 量容器实际矩形，不用 window —— 媒体区域被 CSS 改动后依然算得准
      const r = box.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const iw = media?.naturalWidth || media?.videoWidth || 16;
      const ih = media?.naturalHeight || media?.videoHeight || 9;

      const fit = getComputedStyle(media || box).objectFit === "contain" || stacked;
      const scale = fit ? Math.min(r.width / iw, r.height / ih)
                        : Math.max(r.width / iw, r.height / ih);
      const w = iw * scale, h = ih * scale;
      const left = r.left + (r.width - w) / 2;
      const top  = r.top  + (r.height - h) / 2;

      if (stacked) return;          // 竖屏两种标记都由 CSS 排成列表
      node.querySelectorAll(".hotspot, .pin").forEach(spot => {
        spot.style.left = `${left + Number(spot.dataset.x) * w}px`;
        spot.style.top  = `${top  + Number(spot.dataset.y) * h}px`;
      });
    });
  }

  scene(id) {
    return this.scenes.find(s => s.id === id);
  }

  /* 把 data-src 挂到真 src 上，加载成功才揭幕。
     不要在这之前再发 HEAD 去探测：<img> 自己就有 load/error，
     多一次往返只是多一个失败通道 —— 微信这类内置浏览器和国内代理
     会拦掉或改写 HEAD，探测失败就再也不赋 src，占位符一直留在屏幕上。 */
  async mount(node) {
    const tasks = [];
    for (const media of [node.__poster, node.__loop]) {
      if (!media || media.__mounted) continue;
      media.__mounted = true;
      const isImg = media.tagName === "IMG";
      tasks.push((async () => {
        // 循环视频是可选装饰，多数场景根本没有这个文件 ——
        // 这里留着探测，省掉一串必然 404 的请求。静帧不能这么干：
        // 它是必须出现的东西，探测失败就等于整屏空着。
        if (!isImg && !(await probe(media.dataset.src))) return;

        const attempt = bust => new Promise(done => {
          // 尺寸拿到之后必须重排一次 —— layout() 依赖 naturalWidth
          const ok = () => { media.classList.add("is-on"); this.layout(); done(true); };
          const fail = () => done(false);
          media.addEventListener("error", fail, { once: true });
          media.addEventListener(isImg ? "load" : "loadeddata", ok, { once: true });
          media.src = bust ? `${media.dataset.src}?retry=${bust}` : media.dataset.src;
          if (isImg) { if (media.complete && media.naturalWidth) ok(); }
          else media.load();
        });

        // 移动网络上大图会半路断掉。只试一次的话，一断就永远停在占位符上 ——
        // 这正是手机上看到的样子。隔一会儿再试一次，带个参数绕开可能缓存下来的坏响应。
        if (await attempt(0)) return;
        await new Promise(r => setTimeout(r, 900));
        await attempt(Date.now());
      })());
    }
    await Promise.all(tasks);
  }

  playLoop(node, on) {
    const v = node.__loop;
    if (!v || !v.src) return;
    if (on) v.play().catch(() => {});
    else v.pause();
  }

  async go(id, transitionSrc) {
    if (!this.scene(id) || id === this.current) return;

    if (transitionSrc && (await probe(transitionSrc))) {
      await this.playTransition(transitionSrc);
    }
    this.set(id);
  }

  playTransition(src) {
    return new Promise(resolve => {
      const v = this.transition;
      v.src = src;
      v.currentTime = 0;
      const done = () => {
        v.classList.remove("is-on");
        v.removeEventListener("ended", done);
        setTimeout(resolve, 260);
      };
      v.addEventListener("ended", done);
      v.classList.add("is-on");
      v.play().catch(done);
      // 兜底：视频卡住也别把用户困住
      setTimeout(done, 9000);
    });
  }

  set(id) {
    const node = this.nodes.get(id);
    if (!node) return;

    if (this.current) {
      const prev = this.nodes.get(this.current);
      prev.classList.remove("is-active");
      this.playLoop(prev, false);
    }

    this.current = id;
    document.body.dataset.scene = id;
    node.classList.add("is-active");

    this.mount(node).then(() => this.playLoop(node, true));
    this.prefetchNeighbours(id);
    this.onScene(this.scene(id));
  }

  /* 提前挂载相邻场景，切过去时不用等 */
  prefetchNeighbours(id) {
    const scene = this.scene(id);
    const next = new Set((scene.hotspots || []).map(h => h.to).filter(Boolean));
    if (scene.back) next.add(scene.back);
    const idle = window.requestIdleCallback || (fn => setTimeout(fn, 400));
    next.forEach(target => {
      const node = this.nodes.get(target);
      if (node) idle(() => this.mount(node));
    });
  }
}
