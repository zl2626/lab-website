/**
 * 处理 GitHub Pages / 子路径（base）问题。
 * 所有站内链接统一用 u('/research') 这种写法，
 * 这样无论部署在根域名还是 /repo-name 子路径下都不会 404。
 */
const BASE = import.meta.env.BASE_URL.replace(/\/+$/, ''); // '' 或 '/lab-website'

export function u(path = '/'): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${BASE}${p}` || '/';
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
