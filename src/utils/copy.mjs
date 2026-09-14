/**
 * 后台可配置文案的小工具。
 *
 * 单独成模块是为了让浏览器端脚本也能用（src/lib/content.ts 依赖 astro:content
 * 与 marked，不能被打进前端 bundle）。
 */

/**
 * 替换文案里的占位符，例如 "共 {count} 项" → "共 14 项"。
 * 找不到对应键时保留原样，方便一眼看出哪里还没配。
 */
export function fillCopy(template, values = {}) {
  return String(template ?? '').replace(/\{(\w+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match
  );
}

/** 把逗号分隔的配置项切成数组（用于后台里用逗号分隔的列表型文案） */
export function splitList(value) {
  return String(value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}
