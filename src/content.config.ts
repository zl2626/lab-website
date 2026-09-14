import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * 四个内容集合。每个集合对应 src/content/ 下的一个文件夹。
 * 新增一条内容 = 在对应文件夹里加一个 Markdown 文件（或在 Pages CMS 后台点“新建”）。
 */

// 研究方向
const research = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/research' }),
  schema: z.object({
    title: z.string(), // 中文标题
    titleEn: z.string().optional(), // 英文标题（可选）
    summary: z.string(), // 卡片上的一句话简介
    icon: z.string().default('🔬'), // 卡片图标（emoji）
    order: z.number().default(99), // 排序，越小越靠前
    keywords: z.array(z.string()).default([]),
    cover: z.string().optional(), // 配图路径，如 /images/research/xxx.jpg
    draft: z.boolean().default(false),
  }),
});

// 团队成员
const members = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/members' }),
  schema: z.object({
    name: z.string(), // 中文姓名
    nameEn: z.string().optional(), // 拼音 / 英文名
    // 身份不限制取值，实验室可以自定义（展示分组顺序由后台文案「身份分组顺序」控制）
    role: z.string().default('博士生'),
    title: z.string().optional(), // 职称，如“教授 / 博士生导师”
    order: z.number().default(99), // 组内排序，越小越靠前
    photo: z.string().optional(), // 照片路径，如 /images/team/zhangsan.jpg
    email: z.string().optional(),
    /** 研究兴趣 */
    interests: z.array(z.string()).default([]),
    hobbies: z.array(z.string()).default([]),
    researchFocus: z.string().default(''),
    achievementSummary: z.string().default(''),
    /** 毕业/离开后的去向，例如「某大学 助理教授」 */
    nowAt: z.string().default(''),
    /** 所属研究方向的中文标题，需与研究方向页标题一致，用于在方向详情页列出成员 */
    areas: z.array(z.string()).default([]),
    /** 个人主页 / 学术主页链接 */
    links: z
      .object({
        homepage: z.string().optional(),
        scholar: z.string().optional(),
        github: z.string().optional(),
        orcid: z.string().optional(),
        dblp: z.string().optional(),
      })
      .default({}),
    /** 入学 / 加入年份，用于展示（写 2024 或 "2024" 都可以） */
    joinYear: z.coerce.string().optional(),
    draft: z.boolean().default(false),
  }),
});

// 科研项目 / 基金
const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: z.object({
    name: z.string(), // 项目名称
    /** 常用：国家级项目 / 省部级项目 / 基金项目 / 企业合作 / 国际合作 */
    category: z.string().default(''),
    sponsor: z.string().default(''), // 资助机构
    code: z.string().default(''), // 项目编号
    role: z.string().default(''), // 承担角色，如 主持 / 参与
    leader: z.string().default(''), // 负责人
    /** 参与成员，填团队成员里的姓名 */
    members: z.array(z.string()).default([]),
    startYear: z.coerce.number().optional(),
    endYear: z.coerce.number().optional(),
    /** 常用：在研 / 已结题 */
    status: z.string().default(''),
    amount: z.string().default(''), // 经费，留空则不显示
    summary: z.string().default(''),
    link: z.string().default(''),
    order: z.number().default(99),
    draft: z.boolean().default(false),
  }),
});

// 科研新闻
const news = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/news' }),
  schema: z.object({
    title: z.string(),
    slug: z.string().optional(), // URL 文件名（英文）
    date: z.coerce.date(), // 2026-03-01 这种写法即可
    summary: z.string().optional(), // 列表页摘要
    tags: z.array(z.string()).default([]),
    cover: z.string().optional(),
    pinned: z.boolean().default(false), // 置顶
    draft: z.boolean().default(false),
  }),
});

// 科研成果（论文 / 专利 / 项目）
const publications = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/publications' }),
  schema: z.object({
    title: z.string(), // 论文标题（英文）
    authors: z.array(z.string()).default([]), // 作者列表，本人可用 * 标注
    venue: z.string(), // 期刊 / 会议名称（英文）
    venueShort: z.string().optional(), // 简称，如 CVPR
    year: z.number(),
    type: z.enum(['期刊论文', '会议论文', '预印本', '专利', '专著', '获奖', '项目']).default('会议论文'),
    /** 是否精选（精选会出现在首页） */
    highlight: z.boolean().default(false),
    /** 原文链接（DOI / 会议页） */
    link: z.string().optional(),
    pdf: z.string().optional(),
    code: z.string().optional(),
    /** 所属研究方向，对应 research 的标题 */
    area: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { research, members, news, publications, projects };
