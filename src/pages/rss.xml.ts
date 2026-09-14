/**
 * 科研新闻 RSS。
 *
 * 对标 academicpages / al-folio：给访客和聚合器一个「站点还在更新」的稳定订阅入口。
 */
import type { APIRoute } from 'astro';
import { getNews, getSite } from '../lib/content';

function escapeXml(value: string): string {
  return value.replace(/[&<>"']/g, (char) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[char] as string
  );
}

export const GET: APIRoute = async ({ site }) => {
  const origin = (site ?? new URL('https://example.com')).origin;
  const [info, news] = await Promise.all([getSite(), getNews()]);
  const items = news.slice(0, 30);

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(info.name)} · 科研新闻</title>
    <link>${origin}/news/</link>
    <description>${escapeXml(info.description || info.tagline || `${info.name}的科研新闻与动态`)}</description>
    <language>zh-CN</language>
    <atom:link href="${origin}/rss.xml" rel="self" type="application/rss+xml" />
${items
  .map(
    (item) => `    <item>
      <title>${escapeXml(item.title)}</title>
      <link>${origin}/news/${item.slug}/</link>
      <guid isPermaLink="true">${origin}/news/${item.slug}/</guid>
      <pubDate>${new Date(`${item.date}T00:00:00+08:00`).toUTCString()}</pubDate>
      ${item.summary ? `<description>${escapeXml(item.summary)}</description>` : ''}
${item.tags.map((tag) => `      <category>${escapeXml(tag)}</category>`).join('\n')}
    </item>`
  )
  .join('\n')}
  </channel>
</rss>
`;

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=600',
    },
  });
};
