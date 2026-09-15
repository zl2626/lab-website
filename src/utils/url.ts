/**
 * 处理 GitHub Pages / 子路径（base）问题。
 * 所有站内链接统一用 u('/research') 这种写法，
 * 这样无论部署在根域名还是 /repo-name 子路径下都不会 404。
 */
const BASE = import.meta.env.BASE_URL.replace(/\/+$/, ''); // '' 或 '/lab-website'

/**
 * 站点根地址（来自 astro.config 的 site），用于生成绝对 URL。
 * 注意它**不含**子路径前缀，所以拼绝对地址要配合 u()。
 */
const SITE = import.meta.env.SITE || 'https://example.com';

/** 把站内路径变成带子路径前缀的绝对地址，供 sitemap / RSS / JSON-LD 使用。 */
export function abs(path = '/'): string {
  return new URL(u(path), SITE).toString();
}

export function u(path = '/'): string {
  if (/^https?:\/\//i.test(path)) return path;
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${BASE}${p}` || '/';
}

/**
 * 去掉子路径前缀，得到「站内相对路径」。
 * Astro.url.pathname 在子路径部署下是 /lab-website/research/，
 * 但站内逻辑（面包屑、导航匹配）都按 /research/ 处理。
 */
export function stripBase(pathname: string): string {
  if (BASE && (pathname === BASE || pathname.startsWith(BASE + '/'))) {
    const rest = pathname.slice(BASE.length);
    return rest === '' ? '/' : rest;
  }
  return pathname;
}

/**
 * 图片地址：后端返回的可能是站内路径（/images/...）或完整的 http(s) 链接。
 * 站内路径需要补上 base 前缀，外部链接原样返回。
 */
export function asset(path?: string | null): string {
  if (!path) return '';
  if (/^(https?:)?\/\//i.test(path) || path.startsWith('data:')) return path;
  return u(path);
}
