/**
 * 站内搜索索引。
 *
 * 构建时把全站可检索条目导成一个静态 JSON（数量级很小，一次请求即可全部拿到），
 * 前端在用户第一次打开搜索框时再拉取，所以不会拖慢首屏。
 * 参考 academicpages / Minimal Mistakes 的站内检索做法，但用自己的字段结构，不引入第三方搜索库。
 */
import type { APIRoute } from 'astro';
import { loadContent } from '../lib/content';
import { u } from '../utils/url';

interface SearchEntry {
  /** 结果分组用的类型标识 */
  type: 'research' | 'member' | 'news' | 'publication';
  title: string;
  subtitle: string;
  url: string;
  /** 参与匹配但不直接显示的附加文本 */
  text: string;
}

function clean(parts: (string | undefined | null)[]): string {
  return parts.filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
}

export const GET: APIRoute = async () => {
  const { research, members, news, publications } = await loadContent();

  const entries: SearchEntry[] = [
    ...research.map((item) => ({
      type: 'research' as const,
      title: item.title,
      subtitle: item.titleEn || item.summary,
      url: u(`/research/${item.slug}/`),
      text: clean([item.titleEn, item.summary, item.keywords.join(' '), item.bodyHtml.slice(0, 400)]),
    })),
    ...members.map((item) => ({
      type: 'member' as const,
      title: item.name,
      subtitle: clean([item.role, item.title, item.nowAt]),
      url: u(`/team/${item.slug}/`),
      text: clean([
        item.nameEn,
        item.role,
        item.title,
        item.researchFocus,
        item.nowAt,
        item.interests.join(' '),
        item.hobbies.join(' '),
        item.achievementSummary,
      ]),
    })),
    ...news.map((item) => ({
      type: 'news' as const,
      title: item.title,
      subtitle: item.summary || item.date,
      url: u(`/news/${item.slug}/`),
      text: clean([item.date, item.summary, item.tags.join(' '), item.bodyHtml.slice(0, 400)]),
    })),
    ...publications.map((item) => ({
      type: 'publication' as const,
      title: item.title,
      subtitle: clean([String(item.year), item.venueShort || item.venue, item.type]),
      url: u('/publications/') + `#${item.slug}`,
      text: clean([item.authors.join(' '), item.venue, item.venueShort, item.area, item.abstract]),
    })),
  ];

  return new Response(JSON.stringify({ entries }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
  });
};
