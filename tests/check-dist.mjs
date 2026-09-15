// 构建产物自检：站内断链 + 基础 SEO / 可访问性抽查
// 用法: npm run verify:dist   （需先 npm run build）
import fs from 'node:fs';
import path from 'node:path';

const DIST = 'dist';
if (!fs.existsSync(DIST)) {
  console.error('未找到 dist/，请先执行 npm run build');
  process.exit(1);
}

// BASE_PATH=/lab-website 这类子路径部署（GitHub Pages）时，
// 产物里的站内链接都会带上 /lab-website 前缀。自检脚本必须先把前缀剥掉
// 再比对文件，否则会把所有链接都误报成断链。
const BASE = (process.env.BASE_PATH || '').replace(/\/+$/, '');
function stripBase(url) {
  // 必须要求边界（BASE 本身，或 BASE + '/'），否则 /lab-websitefavicon.svg
  // 这种「少一个斜杠」的真 bug 会被误当成合法链接放过。
  if (BASE && (url === BASE || url.startsWith(BASE + '/'))) {
    const rest = url.slice(BASE.length);
    return rest === '' ? '/' : rest;
  }
  return url;
}

function walk(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, acc);
    else acc.push(p);
  }
  return acc;
}

const skip = (name) => path.basename(name).startsWith('_'); // 忽略本地的临时辅助页

const all = walk(DIST).filter((f) => !skip(f));
const files = new Set(all.map((f) => '/' + path.relative(DIST, f).split(path.sep).join('/')));
const htmlFiles = all.filter((f) => f.endsWith('.html'));

const broken = new Map();
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const re = /(?:href|src)="(\/[^"#?]*)/g;
  let m;
  while ((m = re.exec(html))) {
    const url = m[1];
    const rel = stripBase(url);
    // /api/* 由后端函数处理，不属于静态产物；子路径部署下也要能识别
    if (rel.startsWith('/api/')) continue;
    if (files.has(rel)) continue;
    const candidates = [rel.replace(/\/$/, '') + '/index.html', rel + '/index.html', rel + 'index.html'];
    if (candidates.some((c) => files.has(c))) continue;
    broken.set(url, (broken.get(url) || 0) + 1);
  }
}

console.log(`页面数 ${htmlFiles.length}，资源数 ${files.size}${BASE ? `（子路径前缀 ${BASE}）` : ''}`);
console.log(`断链 ${broken.size} 处`);
for (const [url, count] of broken) console.log(`  ${url} (${count} 处)`);

// 基础规范：每页都应有 lang / title / description / canonical / 唯一 h1，图片都要有 alt
const issues = [];
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const rel = path.relative(DIST, file).split(path.sep).join('/');
  const h1Count = (html.match(/<h1[\s>]/g) || []).length;
  if (!/<html[^>]+lang="/.test(html)) issues.push(`${rel}: 缺少 lang`);
  if (!/<title>[^<]+<\/title>/.test(html)) issues.push(`${rel}: 缺少 title`);
  if (!/name="description" content="[^"]+"/.test(html)) issues.push(`${rel}: 缺少 description`);
  if (!/rel="canonical"/.test(html)) issues.push(`${rel}: 缺少 canonical`);
  if (h1Count !== 1) issues.push(`${rel}: h1 数量为 ${h1Count}`);
  if (/<img(?![^>]*\balt=)[^>]*>/.test(html)) issues.push(`${rel}: 存在没有 alt 的 img`);
}
console.log(`基础规范问题 ${issues.length} 处`);
for (const i of issues) console.log('  ' + i);

if (broken.size > 0 || issues.length > 0) process.exitCode = 1;
