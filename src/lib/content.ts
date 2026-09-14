/**
 * 内容加载层 —— 全站唯一的数据入口。
 *
 * 构建时优先调用后端接口 `${API_BASE}/api/content/`；
 * 未指定 API_BASE 时允许 Markdown 演示模式；指定接口后失败则停止构建。
 * 本地开发默认连接 8000 端口，每次页面请求读取最新保存内容。
 */

import { getCollection } from 'astro:content';
import { marked } from 'marked';

import siteJson from '../data/site.json';
import pageCopySchema from '../../api/core/page_copy.json';

const DEFAULT_COPY = Object.fromEntries(Object.entries(pageCopySchema).map(([key, spec]) => [key, spec.default]));

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

export interface NavLink {
  label: string;
  href: string;
}

export interface SiteInfo {
  name: string;
  nameEn: string;
  abbr: string;
  tagline: string;
  affiliation: string;
  description: string;
  groupPhoto: string;
  contact: { address: string; postcode: string; email: string; phone: string };
  openings: { enabled: boolean; title: string; text: string; detailsHtml: string; email: string };
  nav: NavLink[];
  social: NavLink[];
  icp: string;
  pageCopy: Record<string, string>;
}

export interface ResearchItem {
  slug: string;
  title: string;
  titleEn: string;
  summary: string;
  icon: string;
  keywords: string[];
  order: number;
  cover: string;
  bodyHtml: string;
}

export interface MemberItem {
  slug: string;
  name: string;
  nameEn: string;
  role: string;
  title: string;
  order: number;
  photo: string;
  email: string;
  joinYear: string;
  /** 毕业 / 离开后的去向 */
  nowAt: string;
  /** 所属研究方向的中文标题 */
  areas: string[];
  interests: string[];
  hobbies: string[];
  researchFocus: string;
  achievementSummary: string;
  links: Record<string, string>;
  bioHtml: string;
}

export interface RobotProjectItem { slug: string; name: string; summary: string; researchFocus: string; modelUrl: string; modelFormat: string; demoUrl: string; bodyHtml: string; }

export interface NewsItem {
  slug: string;
  title: string;
  date: string;
  summary: string;
  tags: string[];
  cover: string;
  pinned: boolean;
  bodyHtml: string;
}

export interface PublicationItem {
  slug: string;
  title: string;
  authors: string[];
  venue: string;
  venueShort: string;
  year: number;
  type: string;
  area: string;
  highlight: boolean;
  link: string;
  pdf: string;
  code: string;
  abstract: string;
  bodyHtml: string;
}

export interface ContentBundle {
  source: 'api' | 'markdown';
  site: SiteInfo;
  research: ResearchItem[];
  members: MemberItem[];
  news: NewsItem[];
  publications: PublicationItem[];
  robotProjects: RobotProjectItem[];
}

// ---------------------------------------------------------------------------
// 默认值
// ---------------------------------------------------------------------------

const DEFAULT_NAV: NavLink[] = [
  { label: '首页', href: '/' },
  { label: '研究方向', href: '/research' },
  { label: '团队成员', href: '/team' },
  { label: '科研新闻', href: '/news' },
  { label: '科研成果', href: '/publications' },
  { label: '科研平台', href: '/platform' },
  { label: '联系我们', href: '/contact' },
];

const FALLBACK_SITE: SiteInfo = {
  name: '课题组网站',
  nameEn: '',
  abbr: 'LAB',
  tagline: '',
  affiliation: '',
  description: '',
  groupPhoto: '',
  contact: { address: '', postcode: '', email: '', phone: '' },
  openings: { enabled: false, title: '', text: '', email: '' },
  nav: DEFAULT_NAV,
  social: [],
  icp: '',
  pageCopy: DEFAULT_COPY,
};

// ---------------------------------------------------------------------------
// 工具
// ---------------------------------------------------------------------------

function md(text?: string | null): string {
  if (!text) return '';
  return marked.parse(text, { async: false }) as string;
}

function str(value: unknown, fallback = ''): string {
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function num(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function strList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((item) => String(item));
  if (typeof value === 'string' && value.trim()) {
    return value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function linkList(value: unknown): NavLink[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === 'object')
    .map((item) => ({
      label: str((item as Record<string, unknown>).label),
      href: str((item as Record<string, unknown>).href, '/'),
    }))
    .filter((item) => item.label);
}

/** 把任意后端返回结构规整成 SiteInfo */
function normalizeSite(raw: Record<string, unknown> | null | undefined): SiteInfo {
  if (!raw) return FALLBACK_SITE;
  const contact = (raw.contact ?? {}) as Record<string, unknown>;
  const openings = (raw.openings ?? {}) as Record<string, unknown>;
  return {
    name: str(raw.name, FALLBACK_SITE.name),
    nameEn: str(raw.nameEn),
    abbr: str(raw.abbr, FALLBACK_SITE.abbr),
    tagline: str(raw.tagline),
    affiliation: str(raw.affiliation),
    description: str(raw.description),
    groupPhoto: str(raw.groupPhoto),
    contact: {
      address: str(contact.address),
      postcode: str(contact.postcode),
      email: str(contact.email),
      phone: str(contact.phone),
    },
    openings: {
      enabled: Boolean(openings.enabled),
      title: str(openings.title),
      text: str(openings.text),
      // 接口模式给的是渲染好的 HTML；Markdown 兜底模式下 site.json 里是原始 Markdown，这里补一次渲染
      detailsHtml: str(openings.detailsHtml) || md(str(openings.details)),
      email: str(openings.email),
    },
    nav: linkList(raw.nav).length ? linkList(raw.nav) : DEFAULT_NAV,
    social: linkList(raw.social),
    icp: str(raw.icp),
    pageCopy: { ...DEFAULT_COPY, ...Object.fromEntries(Object.entries((raw.pageCopy ?? {}) as Record<string, unknown>).filter(([, value]) => typeof value === 'string')) } as Record<string, string>,
  };
}

// ---------------------------------------------------------------------------
// 数据源一：后端接口
// ---------------------------------------------------------------------------

function apiBaseCandidates(): string[] {
  const env = (typeof process !== 'undefined' ? process.env : {}) as Record<string, string | undefined>;
  // An explicit source must never fall through to another database or deployment.
  if (env.API_BASE) return [env.API_BASE.replace(/\/+$/, '')];
  const candidates: (string | undefined)[] = [
    env.API_BASE,
    import.meta.env.DEV ? 'http://127.0.0.1:8000' : undefined,
    env.SITE_BASE_URL,
    env.SITE_URL,
    // Vercel 构建时自动注入的「生产域名」，指向当前项目已上线的部署（读同一个数据库）
    env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${env.VERCEL_PROJECT_PRODUCTION_URL}` : undefined,
    // 注意：不要用 VERCEL_URL —— 那指向「正在构建的这个部署」，此时它还没上线，
    // 只会拿到一堆 HTML 并污染构建日志。
  ];
  return [...new Set(candidates.filter((value): value is string => Boolean(value)))].map((value) =>
    value.replace(/\/+$/, '')
  );
}

async function fetchFromApi(): Promise<ContentBundle | null> {
  const bases = apiBaseCandidates();
  if (bases.length === 0) {
    console.info('[content] 未配置 API_BASE，直接使用本地 Markdown 内容。');
    return null;
  }

  for (const base of bases) {
    const url = `${base}/api/content/`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(url, { signal: controller.signal, cache: 'no-store' });

      if (!response.ok) {
        console.warn(`[content] ${url} 返回 ${response.status}，尝试下一个地址。`);
        continue;
      }

      const data = (await response.json()) as Record<string, unknown>;
      if (!data.site || !['research', 'members', 'news', 'publications'].every((key) => Array.isArray(data[key]))) {
        throw new Error('内容接口结构不完整');
      }
      console.info(`[content] ✅ 已从后端接口加载内容：${url}`);
      return {
        source: 'api',
        site: normalizeSite(data.site as Record<string, unknown>),
        research: (Array.isArray(data.research) ? data.research : []).map(normalizeResearch),
        members: (Array.isArray(data.members) ? data.members : []).map(normalizeMember),
        news: (Array.isArray(data.news) ? data.news : []).map(normalizeNews),
        publications: (Array.isArray(data.publications) ? data.publications : []).map(
          normalizePublication
        ),
        robotProjects: (Array.isArray(data.robotProjects) ? data.robotProjects : []).map(normalizeRobotProject),
      };
    } catch (error) {
      console.warn(`[content] ${url} 请求失败：${(error as Error).message}`);
    } finally {
      clearTimeout(timer);
    }
  }

  // Explicitly configured managed builds must not silently publish stale demo content.
  if (process.env.API_BASE && process.env.ALLOW_CONTENT_FALLBACK !== '1') {
    throw new Error('配置的内容接口不可用，已停止构建以避免用示例数据覆盖网站。');
  }
  console.warn('[content] 后端接口不可用，回退到本地 Markdown 内容。');
  return null;
}

function normalizeResearch(raw: unknown): ResearchItem {
  const item = (raw ?? {}) as Record<string, unknown>;
  return {
    slug: str(item.slug),
    title: str(item.title),
    titleEn: str(item.titleEn),
    summary: str(item.summary),
    icon: str(item.icon, '🔬'),
    keywords: strList(item.keywords),
    order: num(item.order, 99),
    cover: str(item.cover),
    bodyHtml: str(item.bodyHtml),
  };
}

function normalizeMember(raw: unknown): MemberItem {
  const item = (raw ?? {}) as Record<string, unknown>;
  const links = (item.links ?? {}) as Record<string, unknown>;
  return {
    slug: str(item.slug),
    name: str(item.name),
    nameEn: str(item.nameEn),
    role: str(item.role, '成员'),
    title: str(item.title),
    order: num(item.order, 99),
    photo: str(item.photo),
    email: str(item.email),
    joinYear: str(item.joinYear),
    nowAt: str(item.nowAt),
    areas: strList(item.areas),
    interests: strList(item.interests),
    hobbies: strList(item.hobbies),
    researchFocus: str(item.researchFocus),
    achievementSummary: str(item.achievementSummary),
    links: Object.fromEntries(
      Object.entries(links)
        .filter(([, value]) => Boolean(value))
        .map(([key, value]) => [key, str(value)])
    ),
    bioHtml: str(item.bioHtml),
  };
}

function normalizeNews(raw: unknown): NewsItem {
  const item = (raw ?? {}) as Record<string, unknown>;
  return {
    slug: str(item.slug),
    title: str(item.title),
    date: str(item.date).slice(0, 10),
    summary: str(item.summary),
    tags: strList(item.tags),
    cover: str(item.cover),
    pinned: Boolean(item.pinned),
    bodyHtml: str(item.bodyHtml),
  };
}

function normalizePublication(raw: unknown): PublicationItem {
  const item = (raw ?? {}) as Record<string, unknown>;
  return {
    slug: str(item.slug),
    title: str(item.title),
    authors: strList(item.authors),
    venue: str(item.venue),
    venueShort: str(item.venueShort),
    year: num(item.year),
    type: str(item.type, '会议论文'),
    area: str(item.area),
    highlight: Boolean(item.highlight),
    link: str(item.link),
    pdf: str(item.pdf),
    code: str(item.code),
    abstract: str(item.abstract),
    bodyHtml: str(item.bodyHtml),
  };
}

function normalizeRobotProject(raw: unknown): RobotProjectItem {
  const item = (raw ?? {}) as Record<string, unknown>;
  return { slug: str(item.slug), name: str(item.name), summary: str(item.summary), researchFocus: str(item.researchFocus), modelUrl: str(item.modelUrl), modelFormat: str(item.modelFormat), demoUrl: str(item.demoUrl), bodyHtml: str(item.bodyHtml) };
}

// ---------------------------------------------------------------------------
// 数据源二：本地 Markdown（兜底）
// ---------------------------------------------------------------------------

async function buildFromMarkdown(): Promise<ContentBundle> {
  const [researchEntries, memberEntries, newsEntries, pubEntries] = await Promise.all([
    getCollection('research', ({ data }) => !data.draft),
    getCollection('members', ({ data }) => !data.draft),
    getCollection('news', ({ data }) => !data.draft),
    getCollection('publications', ({ data }) => !data.draft),
  ]);

  const research: ResearchItem[] = researchEntries
    .map((entry) => ({
      slug: entry.data.slug || entry.id,
      title: entry.data.title,
      titleEn: entry.data.titleEn ?? '',
      summary: entry.data.summary,
      icon: entry.data.icon,
      keywords: entry.data.keywords,
      order: entry.data.order,
      cover: entry.data.cover ?? '',
      bodyHtml: md(entry.body),
    }))
    .sort((a, b) => a.order - b.order);

  const members: MemberItem[] = memberEntries
    .map((entry) => ({
      slug: entry.data.slug || entry.id,
      name: entry.data.name,
      nameEn: entry.data.nameEn ?? '',
      role: entry.data.role,
      title: entry.data.title ?? '',
      order: entry.data.order,
      photo: entry.data.photo ?? '',
      email: entry.data.email ?? '',
      joinYear: entry.data.joinYear ?? '',
      nowAt: entry.data.nowAt ?? '',
      areas: entry.data.areas ?? [],
      interests: entry.data.interests,
      hobbies: entry.data.hobbies,
      researchFocus: entry.data.researchFocus,
      achievementSummary: entry.data.achievementSummary,
      links: Object.fromEntries(
        Object.entries(entry.data.links ?? {}).filter(([, value]) => Boolean(value))
      ) as Record<string, string>,
      bioHtml: md(entry.body),
    }))
    .sort((a, b) => a.order - b.order);

  const news: NewsItem[] = newsEntries
    .map((entry) => ({
      slug: entry.data.slug || entry.id,
      title: entry.data.title,
      date: entry.data.date.toISOString().slice(0, 10),
      summary: entry.data.summary ?? '',
      tags: entry.data.tags,
      cover: entry.data.cover ?? '',
      pinned: entry.data.pinned,
      bodyHtml: md(entry.body),
    }))
    .sort((a, b) => (a.date < b.date ? 1 : -1));

  const publications: PublicationItem[] = pubEntries
    .map((entry) => ({
      slug: entry.data.slug || entry.id,
      title: entry.data.title,
      authors: entry.data.authors,
      venue: entry.data.venue,
      venueShort: entry.data.venueShort ?? '',
      year: entry.data.year,
      type: entry.data.type,
      area: entry.data.area ?? '',
      highlight: entry.data.highlight,
      link: entry.data.link ?? '',
      pdf: entry.data.pdf ?? '',
      code: entry.data.code ?? '',
      abstract: entry.body ?? '',
      bodyHtml: md(entry.body),
    }))
    .sort((a, b) => b.year - a.year || a.title.localeCompare(b.title));

  return {
    source: 'markdown',
    site: normalizeSite(siteJson as unknown as Record<string, unknown>),
    research,
    members,
    news,
    publications,
    robotProjects: [],
  };
}

// ---------------------------------------------------------------------------
// 对外 API（整个构建过程只加载一次）
// ---------------------------------------------------------------------------

let bundlePromise: Promise<ContentBundle> | null = null;

export function loadContent(): Promise<ContentBundle> {
  // Dev pages must read saved database changes instead of keeping the first bundle forever.
  if (import.meta.env.DEV) return (async () => (await fetchFromApi()) ?? (await buildFromMarkdown()))();
  if (!bundlePromise) {
    bundlePromise = (async () => (await fetchFromApi()) ?? (await buildFromMarkdown()))();
  }
  return bundlePromise;
}

export async function getSite(): Promise<SiteInfo> {
  return (await loadContent()).site;
}

export async function getResearch(): Promise<ResearchItem[]> {
  return (await loadContent()).research;
}

export async function getMembers(): Promise<MemberItem[]> {
  return (await loadContent()).members;
}

export async function getNews(): Promise<NewsItem[]> {
  return (await loadContent()).news;
}

export async function getPublications(): Promise<PublicationItem[]> {
  return (await loadContent()).publications;
}

export async function getRobotProjects(): Promise<RobotProjectItem[]> { return (await loadContent()).robotProjects; }
