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

// 站点自身的绝对地址（https://owner.github.io/repo/...）也要当成站内链接检查，
// 否则 abs() 生成的「指向本站的绝对 URL」会绕过断链检测（历史上就这样漏过 404）。
const SITE = (process.env.SITE_URL || '').replace(/\/+$/, '');
// 只有「这个产物自己就有后端」时，/api/* 才不算断链：
// Vercel 由 vercel.json 把 /api/* 交给 Django 函数，本地联调也代理到后端；
// GitHub Pages 是纯静态托管，产物里出现 /api/admin/... 就是必然 404。
// 判据不能只看 API_BASE（那是构建时读内容的地址，可以指向别的后端）。
const HAS_BACKEND = Boolean(process.env.VERCEL || process.env.LOCAL_API === '1');

const broken = new Map();
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const re = /(?:href|src)="(\/[^"#?]*)/g;
  const absRe = SITE ? new RegExp('(?:href|src)="' + SITE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(/[^"#?]*)', 'g') : null;
  const found = [];
  let m;
  while ((m = re.exec(html))) found.push(m[1]);
  if (absRe) while ((m = absRe.exec(html))) found.push(m[1]);
  for (const url of found) {
    const rel = stripBase(url);
    // /api/* 由后端函数处理，不属于静态产物；但没有后端时它就是死链
    if (HAS_BACKEND && rel.startsWith('/api/')) continue;
    if (files.has(rel)) continue;
    const candidates = [
      rel.replace(/\/$/, '') + '/index.html',
      rel + '/index.html',
      rel + 'index.html',
      rel.replace(/\/$/, '') + '.html',
    ];
    if (candidates.some((c) => files.has(c))) continue;
    broken.set(url, (broken.get(url) || 0) + 1);
  }
}

console.log(`页面数 ${htmlFiles.length}，资源数 ${files.size}${BASE ? `（子路径前缀 ${BASE}）` : ''}${SITE ? `，站内绝对地址前缀 ${SITE}` : ''}`);
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

  // Astro 允许把 <script> 写在 </BaseLayout> 之外，编译后会被吐到 </html> 之后。
  // 浏览器能容错执行，但产物已是无效 HTML；这里当成错误拦下来。
  const htmlEnd = html.lastIndexOf(`</html>`);
  if (htmlEnd >= 0 && html.slice(htmlEnd + 7).trim()) {
    issues.push(`${rel}: </html> 之后仍有内容（通常是 <script> 写在了 </BaseLayout> 外面）`);
  }
}
// 首页交付契约：单图首屏、介绍、动态与联系入口。
const home = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8');
if (!home.includes('class="home-hero"')) issues.push('index.html: 缺少单图首页首屏');
if (!home.includes('class="home-latest"')) issues.push('index.html: 缺少实验室最新动态');
if (!home.includes('class="home-intro"')) issues.push('index.html: 缺少实验室介绍');
if (!home.includes('class="home-contact"')) issues.push('index.html: 缺少招聘与联系入口');
if (home.includes('home-carousel') || home.includes('banner-dots')) issues.push('index.html: 仍包含旧轮播');
// 未上传图片时，设计要求使用品牌底色；有图片时必须只加载一个高优先级首屏图。
const heroImages = home.match(/<img[^>]*class="hero-image"[^>]*>/g) || [];
if (heroImages.length > 1) issues.push('index.html: 首屏图片多于一张');
if (heroImages.some((img) => !/fetchpriority="high"/.test(img) || !/loading="eager"/.test(img))) issues.push('index.html: 首屏图片未设置 eager / 高优先级');
if ((home.match(/loading="eager"/g) || []).length !== heroImages.length) issues.push('index.html: 非首屏图片不应 eager 加载');
const contentImages = home.match(/<img[^>]*>/g) || [];
if (contentImages.some((img) => !img.includes('class="hero-image"') && !/loading="lazy"/.test(img))) issues.push('index.html: 下方内容图片未延迟加载');
const navLabels = ['首页', '团队成员', '科研平台', '科研成果', '加入我们'];
const navPos = navLabels.map((label) => home.indexOf(label));
if (navPos.some((pos) => pos < 0) || navPos.some((pos, i) => i > 0 && pos <= navPos[i - 1])) {
  issues.push('index.html: 主导航标签缺失或顺序不正确');
}
if (!/<button[^>]*class="mobile-nav-toggle"[^>]*aria-expanded="false"[^>]*aria-controls="mobile-nav"/.test(home)) {
  issues.push('index.html: 移动导航按钮初始 aria-expanded 不为 false');
}
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const rel = path.relative(DIST, file);
  if (!/<button[^>]*class="mobile-nav-toggle"[^>]*aria-expanded="false"[^>]*aria-controls="mobile-nav"/.test(html)) {
    issues.push(`${rel}: 缺少可访问的移动导航按钮`);
  }
  if (!/<nav[^>]*id="mobile-nav"[^>]*hidden/.test(html)) issues.push(`${rel}: 移动导航初始状态未隐藏`);
}
console.log(`基础规范问题 ${issues.length} 处`);
for (const i of issues) console.log('  ' + i);

if (broken.size > 0 || issues.length > 0) process.exitCode = 1;
