/** 通用格式化工具 */

/** 把 Date 或 ISO 字符串格式化成 2026-06-20 */
export function formatDate(value: string | Date): string {
  if (!value) return '';
  if (typeof value === 'string') {
    // 已经是 YYYY-MM-DD 就直接用，避免时区偏移
    const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (match) return `${match[1]}-${match[2]}-${match[3]}`;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return toISO(parsed);
  }
  return toISO(value);
}

function toISO(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** 头像占位文字：中文取前 2 个字，英文取首字母 */
export function initials(name: string): string {
  const clean = (name || '').trim();
  if (!clean) return '?';
  if (/[\u4e00-\u9fa5]/.test(clean)) {
    return clean.length <= 3 ? clean : clean.slice(0, 2);
  }
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase();
}

/** 按年份分组，年份倒序 */
export function groupByYear<T>(
  items: T[],
  getYear: (item: T) => number
): { year: number; items: T[] }[] {
  const map = new Map<number, T[]>();
  for (const item of items) {
    const year = getYear(item);
    if (!map.has(year)) map.set(year, []);
    map.get(year)!.push(item);
  }
  return [...map.entries()]
    .sort((a, b) => b[0] - a[0])
    .map(([year, list]) => ({ year, items: list }));
}
