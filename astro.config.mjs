// @ts-check
import { defineConfig } from 'astro/config';

// ---------------------------------------------------------------------------
// 站点地址
// ---------------------------------------------------------------------------
// 优先顺序：
//   1. SITE_URL 环境变量（手动指定，最优先）
//   2. Vercel 自动注入的域名（VERCEL_PROJECT_PRODUCTION_URL / VERCEL_URL）
//   3. 本地开发时的占位值
//
// BASE_PATH 用于子路径部署（例如 GitHub Pages 的 /repo-name），
// 部署在 Vercel 时留空即可。
// ---------------------------------------------------------------------------
const vercelHost = process.env.VERCEL_PROJECT_PRODUCTION_URL || process.env.VERCEL_URL;
const site =
  process.env.SITE_URL || (vercelHost ? `https://${vercelHost}` : 'https://your-lab.example.com');
const base = process.env.BASE_PATH || undefined;

export default defineConfig({
  site,
  base,

  trailingSlash: 'ignore',
  build: {
    format: 'directory',
  },
  markdown: {
    shikiConfig: {
      theme: 'github-dark',
    },
  },
});
