/**
 * 自动生成 /robots.txt
 *
 * - 允许搜索引擎抓取全站
 * - 禁止抓取 /api/（后台与接口不需要收录）
 * - 声明站点地图位置
 */

import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ site, url }) => {
  const origin = (site ?? url).origin;

  const body = [
    'User-agent: *',
    'Allow: /',
    'Disallow: /api/',
    '',
    '# 百度 / Google 通用：提交站点地图可加快收录',
    `Sitemap: ${origin}/sitemap.xml`,
    '',
  ].join('\n');

  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
