/**
 * 为正文标题生成锚点，并收集目录。
 *
 * 正文来自 Markdown 渲染（后端用 python-markdown，兜底用 marked），两边默认都不带 id，
 * 所以在这里统一补上：既能做页内目录跳转，也方便外部链接直接定位到某一小节。
 */

const HEADING_RE = /<h([1-6])((?:\s[^>]*)?)>([\s\S]*?)<\/h\1>/gi;

function stripTags(html) {
  return String(html ?? '')
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

/**
 * 生成锚点 id：保留中英文与数字（中文 id 在 HTML5 里完全合法，也比 `section-3` 可读），
 * 其余字符折叠成连字符。
 */
export function slugifyHeading(text) {
  return (
    String(text ?? '')
      .trim()
      .toLowerCase()
      .replace(/[\s\u3000]+/g, '-')
      .replace(/[^\p{Letter}\p{Number}\-_]/gu, '')
      .replace(/-{2,}/g, '-')
      .replace(/^-+|-+$/g, '') || 'section'
  );
}

/**
 * 给 html 里的标题补 id，并返回 { html, headings }。
 * headings 里只保留 h2 / h3 —— 目录再深就没有阅读价值了。
 */
export function withHeadingAnchors(html) {
  const headings = [];
  const used = new Set();

  const output = String(html ?? '').replace(HEADING_RE, (match, level, attrs = '', inner) => {
    const text = stripTags(inner).replace(/\s+/g, ' ').trim();
    if (!text) return match;

    const existing = attrs.match(/\bid\s*=\s*["']([^"']+)["']/i);
    if (existing) {
      used.add(existing[1]);
      if (Number(level) <= 3) headings.push({ level: Number(level), id: existing[1], text });
      return match;
    }

    const base = slugifyHeading(text);
    let id = base;
    let suffix = 2;
    while (used.has(id)) id = `${base}-${suffix++}`;
    used.add(id);

    if (Number(level) <= 3) headings.push({ level: Number(level), id, text });
    return `<h${level}${attrs} id="${id}">${inner}</h${level}>`;
  });

  return { html: output, headings };
}

/** 目录条目少于这个数量就不显示目录（太短的文章不需要） */
export const TOC_MIN_HEADINGS = 3;

export function shouldShowToc(headings) {
  return Array.isArray(headings) && headings.length >= TOC_MIN_HEADINGS;
}
