/**
 * 站内搜索的纯逻辑部分：分词、打分排序、命中高亮。
 * 与 DOM 无关，方便单独做单元测试（见 tests/search.test.mjs）。
 */

/** 把查询串拆成小写关键词（空格分隔，支持中英文混排） */
export function tokenize(query) {
  return String(query || '')
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
}

export function escapeHtml(value) {
  return String(value ?? '').replace(
    /[&<>"']/g,
    (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]
  );
}

/**
 * 打分规则：完全相等 > 标题前缀 > 标题包含 > 副标题包含 > 正文包含。
 * 命中位置越靠前分数越高；所有关键词都必须命中（AND 语义），否则整体不匹配（返回 -1）。
 */
export function scoreEntry(entry, tokens) {
  if (!tokens.length) return -1;
  const title = String(entry.title || '').toLowerCase();
  const subtitle = String(entry.subtitle || '').toLowerCase();
  const text = String(entry.text || '').toLowerCase();

  let total = 0;
  for (const token of tokens) {
    let best = -1;
    if (title === token) best = 1000;
    else if (title.startsWith(token)) best = 600 - title.indexOf(token);
    else if (title.includes(token)) best = 400 - title.indexOf(token);
    else if (subtitle.includes(token)) best = 200;
    else if (text.includes(token)) best = 100;
    if (best < 0) return -1;
    total += best;
  }
  return total;
}

/** 按相关度排序并截断；同分时保持索引里的原始顺序（研究方向 → 成员 → 新闻 → 成果） */
export function searchEntries(entries, query, limit = 18) {
  const tokens = tokenize(query);
  if (!tokens.length) return [];
  return (Array.isArray(entries) ? entries : [])
    .map((entry, index) => ({ entry, index, value: scoreEntry(entry, tokens) }))
    .filter((row) => row.value >= 0)
    .sort((a, b) => b.value - a.value || a.index - b.index)
    .slice(0, limit)
    .map((row) => row.entry);
}

/** 把命中的关键词包成 <mark>；会先做 HTML 转义，可安全用于 innerHTML */
export function highlightMatches(text, tokens) {
  let output = escapeHtml(text);
  for (const token of tokens) {
    if (!token) continue;
    const pattern = escapeHtml(token).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    output = output.replace(new RegExp(`(${pattern})`, 'gi'), '<mark>$1</mark>');
  }
  return output;
}
