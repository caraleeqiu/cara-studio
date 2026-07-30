# 柜台对话的后端

三步部署：

```bash
cd worker
npx wrangler deploy
npx wrangler secret put GEMINI_API_KEY     # 粘贴 key，不会进代码库
```

部署完拿到一个地址，形如 `https://cara-studio-chat.<你的账号>.workers.dev`，
把它填进 [../src/config.js](../src/config.js)：

```js
export const CHAT_WORKER = "https://cara-studio-chat.xxx.workers.dev";
```

上线后记得把线上域名加进 `wrangler.toml` 的 `ALLOWED_ORIGINS`，
否则线上站点会被 Worker 拒掉。

## 为什么要有这一层

key 不能进前端。任何写在网页里的 key，别人打开开发者工具就能拿走，
然后用你的额度跑他们自己的东西。Worker 是唯一存 key 的地方。

`PER_MINUTE = 8` 是同 IP 每分钟上限。作品集不需要更多，
而这一条是账单不失控的唯一防线。
