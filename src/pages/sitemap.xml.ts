/**
 * 自动生成 /sitemap.xml
 *
 * URL 直接从内容层枚举，所以后台新增成员 / 新闻 / 方向都会自动出现在站点地图里。
 * 部署后到百度搜索资源平台、Google Search Console 提交这个地址即可。
 */

import type { APIRoute } from 'astro';

import { loadContent } from '../lib/content';
import { abs } from '../utils/url';

const ESCAPES: Record<string, string> = {
  '<': '&lt;',
  '>': '&gt;',
  '&': '&amp;',
  "'": '&apos;',
  '"': '&quot;',
};

function esc(value: string): string {
  return value.replace(/[<>&'"]/g, (char) => ESCAPES[char] ?? char);
}

interface Entry {
  path: string;
  priority: string;
  changefreq: string;
  lastmod?: string;
}

export const GET: APIRoute = async () => {
  const { research, members, news } = await loadContent();

  const entries: Entry[] = [
    { path: '/', priority: '1.0', changefreq: 'weekly' },
    { path: '/research/', priority: '0.9', changefreq: 'monthly' },
    { path: '/publications/', priority: '0.9', changefreq: 'weekly' },
    { path: '/projects/', priority: '0.8', changefreq: 'monthly' },
    { path: '/team/', priority: '0.8', changefreq: 'monthly' },
    { path: '/news/', priority: '0.8', changefreq: 'weekly' },
    { path: '/join/', priority: '0.8', changefreq: 'monthly' },
    { path: '/contact/', priority: '0.5', changefreq: 'yearly' },
    { path: '/platform/', priority: '0.8', changefreq: 'monthly' },
  ];

  for (const item of research) {
    entries.push({ path: `/research/${item.slug}/`, priority: '0.8', changefreq: 'monthly' });
  }
  for (const item of members) {
    entries.push({ path: `/team/${item.slug}/`, priority: '0.6', changefreq: 'monthly' });
  }
  for (const item of news) {
    entries.push({
      path: `/news/${item.slug}/`,
      priority: '0.7',
      changefreq: 'yearly',
      lastmod: item.date,
    });
  }

  const body = entries
    .map((entry) => {
      // abs() 会带上子路径前缀（GitHub Pages 的 /lab-website）
      const lines = [`    <loc>${esc(abs(entry.path))}</loc>`];
      if (entry.lastmod) lines.push(`    <lastmod>${entry.lastmod}</lastmod>`);
      lines.push(`    <changefreq>${entry.changefreq}</changefreq>`);
      lines.push(`    <priority>${entry.priority}</priority>`);
      return `  <url>\n${lines.join('\n')}\n  </url>`;
    })
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
