# 开源项目参考与本轮落地

调研日期：2026-09-13。本轮参考产品设计思路，自行实现适配现有项目的代码，未引入或复制下列项目的框架源码。

| 参考项目 | 参考方向 | 本项目实现 |
| --- | --- | --- |
| [al-folio](https://github.com/alshedivat/al-folio) | 学术网站的成果与文献组织 | 成果摘要展开、BibTeX 展示与下载 |
| [Django Unfold](https://github.com/unfoldadmin/django-unfold) | 清晰的后台工作台与导航 | 草稿快捷入口、按权限展示的最近更新 |
| [Wagtail](https://github.com/wagtail/wagtail) | 面向内容编辑者的管理体验 | 作者、关键词、兴趣、标签改为逐行输入，同时兼容历史 JSON 数组 |

## 实现边界

- 保留 Astro 静态官网和 Django Admin；页面文案通过新增的 `SiteSetting.page_copy` 字段保存，需执行 `0003` 迁移，本地已完成。
- 引用只使用已有元数据，不补写 DOI、页码或卷期；下载前提示核对原文。原有示例数据仍是示例数据。
- 后台最近更新仅显示账号有权查看或修改的模型，不扩大现有权限。
- 列表输入保留顺序与姓名中的逗号；每行保存为一个字符串，接口数据结构不变。

## 验证

```powershell
.venv/Scripts/python.exe api/manage.py test core --settings=labbackend.test_settings
node --test tests/bibtex.test.mjs
npm run build
```

## 内容管理联调

参考 Wagtail 的编辑分组方式，站点设置新增首页、研究方向页、成员页、新闻页、成果页、联系页和页脚文案。导航与外部链接提供格式校验。研究配图、新闻封面和成员照片支持上传与前台展示。

本地开发默认连接 `127.0.0.1:8000`，保存后刷新前台读取数据库。生产环境仍为静态构建，需指定 `API_BASE` 并配置发布服务。指定接口失败时默认停止构建，避免旧示例内容覆盖已维护内容。

运行前后端服务后，可执行 `.venv/Scripts/python.exe tests/verify_local_content.py`。脚本仅操作本地 SQLite，通过后台保存测试文案，检查六个页面和页脚，并在 `finally` 中恢复原设置；运行时请暂停编辑站点设置。

## 第二轮：对标主流开源学术站点补齐能力（2026-09-14）

调研了 GitHub 上 star 数最高的一批学术站点方案，以及若干高校发布的实验室网站规范，
找出我们这个站点明显缺失、且对访客真正有用的部分，然后自己实现。

| 参考项目 / 规范 | 参考的具体能力 | 本项目实现 |
| --- | --- | --- |
| [academicpages](https://github.com/academicpages/academicpages.github.io)（17.4k star）<br>[Minimal Mistakes](https://github.com/mmistakes/minimal-mistakes)（13.4k star） | 站内检索、结构化文献列表 | ⌘K 站内搜索：构建时生成静态索引，支持中英文关键词、分组展示、键盘操作与命中高亮 |
| [al-folio](https://github.com/alshedivat/al-folio)（16k star） | team directory、Google Scholar 引用、自动明暗主题 | 成员增加「毕业去向」与「所属研究方向」；研究方向详情页反查本方向成员 |
| [Academic-project-page-template](https://github.com/eliahuhorwitz/Academic-project-page-template)（5.1k star） | 一键复制引用、BibTeX 展示 | 成果条目增加「复制引用」；成果页支持把当前筛选结果导出为一个 .bib |
| [HugoBlox](https://github.com/HugoBlox/hugo-theme-academic-cv)（5k star） | BibTeX 导入、学术 SEO | 结构化数据补成 `@graph`：机构 + WebSite/SearchAction + 面包屑，详情页再叠加 `Person` / `NewsArticle` |
| [Gribble Lab《How to design your academic website》](https://gribblelab.org/) | Join Us 要写清材料、流程、导师理念；列出校友去向 | 招生区块支持 Markdown 详情（我们在找什么样的人 / 申请材料 / 申请流程 / 常见问题）；校友卡片突出「现在在哪」 |
| WVU 等高校 [Faculty and Lab Website Guidelines](https://webstandards.wvu.edu/general-guidelines/faculty-and-lab-website-guidelines) | 可访问性（WCAG）、持续更新的可见性 | 补齐跳转链接、焦点轮廓、`h1` 唯一性；新增新闻 RSS 与构建产物自检脚本 |

### 这一轮的具体改动

**后端**（`0006` 迁移）

- `Member.now_at`：毕业 / 离开后的去向，校友卡片与个人页会突出显示。
- `Member.areas`：所属研究方向（填中文标题），用于研究方向详情页反查成员。
- `SiteSetting.openings_details`：招生详情，存 Markdown，接口返回渲染后的 HTML。

**前台**

- 站内搜索（`src/pages/search-index.json.ts` + `src/components/SearchDialog.astro`），
  打分与高亮逻辑抽到 `src/utils/search.mjs` 并有单测覆盖。
- 结构化数据、面包屑、回到顶部、打印样式、新闻 RSS、404 页快捷入口。
- 成果的引用能力：复制到剪贴板 + 按筛选导出 `.bib`（`src/utils/clipboard.mjs`）。

### 已知取舍

- 没有引入第三方搜索服务（Algolia / Lunr）：全站条目只有几十条，静态索引一次拉取即可，省掉一个外部依赖。
- 没有做「项目 / 基金」独立板块：现有「科研成果」的类型里已有「项目」，基金信息可以先写进方向正文或新闻；
  等真的需要按资助机构聚合时再单独建模。
- 没有接入 Google Scholar 引用数：需要第三方服务或爬取，与「只使用已有元数据、不编造数据」的原则冲突，
  因此只通过 `sameAs` 指向学者的 Scholar 主页。

