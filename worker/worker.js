/* Cloudflare Worker：柜台对话的后端。
 *
 * 做三件事：
 *   1. 代理模型 API —— key 只存在 Worker 的环境变量里，永远不进前端
 *   2. SSE 流式返回 —— 前端边收边吐气泡，不用等整段
 *   3. 频率限制 —— 不然 key 会被刷爆
 *
 * 部署：
 *   npx wrangler deploy
 *   npx wrangler secret put GEMINI_API_KEY
 * 然后把地址填进 src/config.js 的 CHAT_WORKER。
 */

const MODEL = "gemini-2.5-flash";
const API = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:streamGenerateContent?alt=sse&key=`;

/* 同一个 IP 每分钟最多这么多次。作品集不需要更多，
   而这一条是 key 不被刷爆的唯一防线。 */
const PER_MINUTE = 8;
const MAX_CHARS = 600;      // 单条输入上限
const MAX_TURNS = 12;       // 只带最近几轮，省 token 也防注入长文

const hits = new Map();     // ip -> [timestamps]，Worker 实例内存，够用

function rateLimited(ip) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter(t => now - t < 60_000);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 5000) hits.clear();   // 防内存无限涨
  return recent.length > PER_MINUTE;
}

const cors = origin => ({
  "Access-Control-Allow-Origin": origin || "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
});


/* ---------------------------------------------------------------- 留言墙
 * 和 Q Studio 一样做成公开的：GET 拿列表，POST 写一条。
 * 存在 KV 里，所以访客能看到别人留的 —— 这是留言墙和联系表单的区别。
 */
const NOTES_KEY = "notes";
const MAX_NOTES = 60;
const NAME_MAX = 24;
const TEXT_MAX = 300;

async function readNotes(env) {
  if (!env.NOTES) return [];
  try { return JSON.parse((await env.NOTES.get(NOTES_KEY)) || "[]"); }
  catch { return []; }
}

async function handleNotes(request, env, origin) {
  if (!env.NOTES) {
    return json({ error: "KV not bound" }, 501, origin);
  }

  if (request.method === "GET") {
    // 只回公开字段，不回 owner token
    const notes = (await readNotes(env)).map(({ name, text, at }) => ({ name, text, at }));
    return json({ notes }, 200, origin);
  }

  let body;
  try { body = await request.json(); }
  catch { return json({ error: "Bad JSON" }, 400, origin); }

  const name = String(body.name || "").trim().slice(0, NAME_MAX);
  const text = String(body.text || "").trim().slice(0, TEXT_MAX);
  if (!name || !text) return json({ error: "Empty" }, 400, origin);

  const notes = await readNotes(env);
  notes.unshift({ name, text, at: new Date().toISOString() });
  await env.NOTES.put(NOTES_KEY, JSON.stringify(notes.slice(0, MAX_NOTES)));

  return json({ ok: true, notes: notes.slice(0, MAX_NOTES).map(({ name, text, at }) => ({ name, text, at })) },
              200, origin);
}

const json = (obj, status, origin) => new Response(JSON.stringify(obj), {
  status,
  headers: { ...cors(origin), "Content-Type": "application/json" },
});

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    const path = new URL(request.url).pathname;

    // 留言墙。GET 也要放行，所以在来源检查之前拿到 path。
    if (path.endsWith("/notes")) {
      if (request.method !== "GET" && request.method !== "POST") {
        return new Response("Method not allowed", { status: 405, headers: cors(origin) });
      }
      if (request.method === "POST") {
        const ip0 = request.headers.get("CF-Connecting-IP") || "unknown";
        if (rateLimited(ip0)) {
          return new Response("Slow down", { status: 429, headers: cors(origin) });
        }
      }
      return handleNotes(request, env, origin);
    }

    if (request.method !== "POST" || !path.endsWith("/chat")) {
      return new Response("Not found", { status: 404, headers: cors(origin) });
    }

    // 只允许自己的站点调用，避免别人拿去当免费 API
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
    if (allowed.length && !allowed.some(a => origin === a)) {
      return new Response("Forbidden", { status: 403, headers: cors(origin) });
    }

    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    if (rateLimited(ip)) {
      return new Response("Slow down", { status: 429, headers: cors(origin) });
    }

    let body;
    try { body = await request.json(); }
    catch { return new Response("Bad JSON", { status: 400, headers: cors(origin) }); }

    const persona = String(body.persona || "").slice(0, 8000);
    const messages = (Array.isArray(body.messages) ? body.messages : [])
      .slice(-MAX_TURNS)
      .map(m => ({
        role: m.role === "assistant" ? "model" : "user",
        parts: [{ text: String(m.content || "").slice(0, MAX_CHARS) }],
      }))
      .filter(m => m.parts[0].text);

    if (!messages.length) {
      return new Response("Empty", { status: 400, headers: cors(origin) });
    }

    const upstream = await fetch(API + env.GEMINI_API_KEY, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: persona }] },
        contents: messages,
        generationConfig: { temperature: 0.85, maxOutputTokens: 400 },
      }),
    });

    if (!upstream.ok || !upstream.body) {
      return new Response("Upstream error", { status: 502, headers: cors(origin) });
    }

    /* Gemini 的 SSE 结构和前端要的不一样，这里转成
       { delta } 的简单格式，前端只管取 delta。 */
    const { readable, writable } = new TransformStream();
    (async () => {
      const writer = writable.getWriter();
      const enc = new TextEncoder();
      const dec = new TextDecoder();
      const reader = upstream.body.getReader();
      let buf = "";
      try {
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
              const text = j?.candidates?.[0]?.content?.parts?.map(p => p.text).join("") || "";
              if (text) await writer.write(enc.encode(`data: ${JSON.stringify({ delta: text })}\n\n`));
            } catch { /* 半截 chunk，等下一轮 */ }
          }
        }
        await writer.write(enc.encode("data: [DONE]\n\n"));
      } finally {
        await writer.close();
      }
    })();

    return new Response(readable, {
      headers: {
        ...cors(origin),
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
      },
    });
  },
};
