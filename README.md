# 课题组网站

## 前台能力补充（2026-09-14 · 第二轮）

对标 academicpages / al-folio / HugoBlox / Academic-project-page-template 这批主流开源学术站点后补齐的能力：

- **站内搜索**：按 `⌘K`（Windows 为 `Ctrl+K`）或点顶栏搜索按钮打开，也支持在页面空白处按 `/`。
  支持中英文关键词、按栏目分组、`↑↓` 选择、`Enter` 打开、命中高亮。
  索引在构建时生成（`/search-index.json`），第一次打开搜索框时才拉取，不拖慢首屏；
  也支持 `/?q=关键词` 直接带词进入。
- **引用**：成果条目新增「复制引用」（写入剪贴板并给出反馈）；
  成果页可按当前筛选结果一键导出 `.bib`，用于 Zotero / EndNote / BibDesk。
- **学术结构化数据**：全站输出 `ResearchOrganization` + `WebSite`（含 `SearchAction`）+ 面包屑；
  成员页额外输出 `Person`（含 `sameAs` 学术主页），新闻页额外输出 `NewsArticle`。
- **成员去向**：后台「团队成员」新增「现在在哪 / 毕业去向」，校友卡片与个人页会突出显示。
- **方向关联成员**：后台成员填「所属研究方向」后，研究方向详情页会自动列出该方向成员。
- **招生详情**：后台「站点设置 → 招生信息」新增 Markdown 详情字段，
  可写申请材料、流程、常见问题，展示在联系页招生区块下方。
- **其他**：新闻 RSS（`/rss.xml`）、长页面回到顶部、404 页搜索与栏目快捷入口、打印样式。
- 新增自检脚本 `npm run verify:dist`，并新增 `tests/search.test.mjs` 覆盖搜索排序与高亮逻辑。

调研结论、参考项目与已知取舍记录在 [docs/project-references.md](docs/project-references.md)。

## 内容导入补充（2026-09-14）

`seed_content` 支持从 `src/data/site.json` 导入 `groupPhoto`（团队合影）和 `pageCopy`（页面文案）。文案按键合并，未提供的键保留后台现有值。

成员 Markdown 可设置 `hobbies`（字符串数组）、`researchFocus`（研究重点）、`achievementSummary`（成果概述）；这些字段同时用于静态页面和数据库导入。旧文件省略这些字段时，导入不会清空后台已维护的扩展资料；显式填写空数组或空字符串可清空对应资料。

验证命令：`npm test`、`npm run build`；后端测试使用 `.venv/Scripts/python.exe api/manage.py test core --settings=labbackend.test_settings`，在独立测试数据库中运行。

## 前台视觉与自检补充（2026-09-14）

- **导航条**不再使用写死的灰色渐变（原样式在深色主题下是一块浅灰，非常突兀），改为跟随主题变量；
  首页顶栏默认是覆盖在大图上的透明浮层，滚过首屏后过渡为实底。移动端横向滚动时右侧有渐隐遮罩作为提示。
- **吸顶偏移量**改用 `--header-h` 变量，由脚本按顶栏实测高度写入（`ResizeObserver` + 字体加载完成后校准），
  不再写死像素值；成果页的年份吸顶标题、锚点滚动偏移都依赖它。
- **首页新增「代表性成果」栏目**（优先展示 `highlight` 成果，最多 4 条，2×2 排列），
  并给研究方向、近况栏目补上引导语。对应后台「页面文案 → 首页」中的
  `home_publications_title/intro/more`、`home_research_intro`、`home_news_intro`。
  与原「近况」栏目语义重复的 `home_updates_*` 三个键已移除，改完内容后需要重建前台。
- **首页轮播**新增自动播放（悬停/键盘聚焦时暂停）、圆点切换、左右方向键；
  每页只保留一个 `h1`（第一张标题用 `h1`，其余用 `h2`），避免搜索结果里出现多个主标题。
- **团队成员卡片**改为自适应列宽（桌面最多 3 列），窄屏保持头像与文字横向排布，卡片不再被拉得过高。
- 清理了 `api/core/forms.py` 中重复的链接校验分支，以及未使用的样式规则。

构建产物自检（会检查站内断链、`title`/`description`/`canonical`、`h1` 唯一性、图片 `alt`）：

```bash
npm run build && npm run verify:dist
```

用无头 Chrome 截图复核视觉（脚本在 `_shots/`，该目录不入库）：

```bash
# 先起静态预览：.venv/Scripts/python.exe -m http.server 4321 --directory dist --bind 127.0.0.1
bash _shots/shoot.sh              # 桌面 1440
W=390 bash _shots/shoot.sh        # 真·移动端（iframe 固定视口，绕开 Chrome 最小窗口宽度限制）
DARK=1 bash _shots/shoot.sh       # 深色主题
```

注意：直接给无头 Chrome 传 `--window-size=390,...` 拿不到真实移动端布局（Windows 下窗口有最小宽度），
必须走 `_shots/frame.html` 里的固定宽度 iframe。

一个课题组 / 实验室官网，包含**研究方向、团队成员、科研新闻、科研成果**四大板块。

- **前台**：Astro 构建为纯静态 HTML，SEO 好、加载快
- **后台**：Django Admin，管理员在网页上动态维护全部内容
- **数据**：PostgreSQL 数据库
- **部署**：一个 GitHub 仓库 → 一个 Vercel 项目（静态前端 + Django 函数）

---

## 一、架构总览

```
                         ┌─────────────────────────── Vercel 项目 ───────────────────────────┐
                         │                                                                    │
  浏览器 ──GET /─────────┼──▶ 静态文件（Astro 构建产物 dist/）                                 │
                         │                                                                    │
  浏览器 ──GET /api/*────┼──▶ api/index.py ──▶ Django（WSGI 函数）──▶ PostgreSQL              │
                         │                      ├── /api/admin/   后台管理界面                │
                         │                      ├── /api/content/ 前端构建时拉取的内容        │
                         │                      └── /api/static/  Admin 的 CSS/JS             │
                         │                                                                    │
  构建时（Vercel Build）──┼──▶ npm run build ──▶ 请求 /api/content/ ──▶ 生成静态页面           │
                         └────────────────────────────────────────────────────────────────────┘
```

**内容更新流程**：管理员在 `/api/admin/` 改内容 → 数据库更新 → 点后台动作「🚀 重建前台站点」
→ 触发 Vercel Deploy Hook → 前端重新构建（构建时从 `/api/content/` 拉最新数据）→ 约 1 分钟上线。

**为什么前端是"构建时拉取"而不是"浏览器实时拉取"**：
这样产出的是纯静态 HTML，百度 / Google 都能正常收录，首屏也更快。
代价是改完内容要等一次重建（约 1 分钟）。

---

## 二、目录结构

```
实验室网站/
├── api/                            # ★ Django 后端（部署为 Vercel 函数）
│   ├── index.py                    #   Vercel 入口，导出 WSGI 的 app
│   ├── manage.py                   #   Django 命令行
│   ├── labbackend/                 #   Django 项目配置
│   │   ├── settings.py             #   数据库 / 环境变量 / 静态文件配置
│   │   ├── urls.py                 #   全部路由都挂在 /api/ 前缀下
│   │   └── wsgi.py
│   └── core/                       #   业务应用
│       ├── models.py               #   6 个数据模型（含图片文件表）
│       ├── admin.py                #   ★ 后台管理界面配置
│       ├── media.py                #   图片上传：压缩 + 存进数据库
│       ├── widgets.py              #   后台「上传 或 粘贴链接」二合一字段
│       ├── views.py                #   公开 JSON 接口 + 图片访问
│       ├── serializers.py          #   模型 → JSON
│       ├── ai.py                   #   DeepSeek 封装（可选）
│       ├── migrations/             #   数据库迁移
│       ├── static/core/            #   后台上传控件的样式与脚本
│       ├── templates/core/         #   后台上传控件的模板
│       └── management/commands/seed_content.py   # 从 Markdown 导入初始内容
│
├── src/                            # ★ Astro 前端
│   ├── lib/content.ts              #   内容加载层：优先 API，失败回退 Markdown
│   ├── data/site.json              #   站点信息（同时也是兜底数据）
│   ├── content/                    #   Markdown 内容（兜底 + 导入数据库的种子）
│   │   ├── research/  members/  news/  publications/
│   ├── pages/
│   │   ├── sitemap.xml.ts          #   自动生成站点地图
│   │   └── robots.txt.ts           #   自动生成 robots.txt
│   ├── components/  layouts/  styles/
│   └── utils/
│
├── public/images/                  # 图片（team/ 成员照片，research/ 方向配图）
├── requirements.txt                # Python 依赖（Vercel 自动安装）
├── vercel.json                     # ★ Vercel 部署、路由与安全响应头配置
├── .vercelignore                   # 部署时不上传的文件（本地数据库、构建产物等）
├── .env.example                    # 环境变量示例
└── astro.config.mjs
```

---

## 三、本地开发

### 1. 前端

```bash
npm install
npm run dev            # http://localhost:4321
```

此时没有后端，前端会自动使用 `src/content/` 里的 Markdown 内容（兜底模式）。

### 2. 后端（可选，想调后台时再开）

```bash
# 安装 Python 依赖
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# 建表 + 导入 Markdown 初始内容 + 创建管理员
python api/manage.py migrate
python api/manage.py seed_content
python api/manage.py createsuperuser

# 启动后端
python api/manage.py runserver 127.0.0.1:8000
# 后台：http://127.0.0.1:8000/api/admin/
```

### 3. 前端连后端（验证 API 模式）

```bash
API_BASE=http://127.0.0.1:8000 npm run build
# 构建日志会打印：[content] ✅ 已从后端接口加载内容：...
```

不设 `API_BASE` 时走 Markdown 兜底，两种模式都能构建成功。

---

## 四、内容管理（Django Admin）

### 页面数据与保存

「站点设置」中可展开首页、研究方向页、成员页、新闻页、成果页、联系页及页脚分组，修改页面标题、介绍、栏目按钮、地图链接、到访说明和版权文案。成员、新闻、成果与研究方向的具体内容仍在各自菜单维护。数量由数据库自动统计，筛选控件等功能性标签由代码维护。

本地前后台同时运行时，保存后刷新 `http://127.0.0.1:4321/` 即可看到更新；图片通过前端的 `/api` 代理加载。线上是静态网站，保存后仍需成功重建。明确设置 `API_BASE` 后，接口失败默认阻止构建；仅在需要演示兜底时设置 `ALLOW_CONTENT_FALLBACK=1`。

已有环境升级请先备份数据库，再运行 `python api/manage.py migrate`，新增页面文案字段不会替换现有内容。

本地保存联调：`.venv/Scripts/python.exe tests/verify_local_content.py`。需要两个开发服务运行；脚本验证六个页面和页脚，自动恢复原文案，执行期间请暂停修改站点设置。

### 成员信息与科研平台

团队成员编辑页提供照片、兴趣爱好、主要研究方向和成果产出，字段名称按日常语言设计；成员详情页会展示这些内容。

「科研平台·机器人项目」用于记录机器人项目。每个项目可以填写项目介绍、研究方向、3D 模型格式和模型地址、演示视频地址、详细说明，并用“发布”控制是否在前台显示。3D 模型和视频建议上传到 GitHub Releases、对象存储、网盘或视频平台后粘贴公开地址；Vercel 函数不适合保存大文件。前台入口是 `/platform`。

登录 `/api/admin/` 后，工作台会展示当前账号可管理内容的总数、已发布数、草稿数和新增入口。
这些数量表示数据库里的内容状态，不表示当前线上构建已经同步。

超级管理员可在工作台点击「重建并发布官网」，无需先选择内容记录。
按钮通过带 CSRF 校验的 POST 请求触发重建；普通编辑者仍可按分配的权限维护内容。
工作台会提示自动发布是否开启、发布服务是否配置；请求成功后需到部署平台确认构建结果。

内容菜单如下：

| 菜单 | 说明 |
| --- | --- |
| 站点设置 | 课题组名称、简介、联系方式、招生信息、导航菜单、页脚链接 |
| 研究方向 | 带图标、关键词、排序、配图、Markdown 正文 |
| 团队成员 | 身份分组（导师/博士后/博士生/硕士生/本科生/科研助理/校友）、**照片上传**、链接 |
| 科研新闻 | 日期、标签、置顶、封面图、Markdown 正文；支持「用 AI 根据正文生成摘要」 |
| 科研成果 | 作者、期刊会议、年份、类型、所属方向、精选、原文/PDF/代码链接 |
| 图片文件 | 已上传图片的汇总，可查看和清理 |

### 上传成员照片 / 封面图

成员表单里的「照片」和新闻的「封面图」都是一个**二合一字段**：

- 点 **「选择图片…」** 从电脑或手机相册选图 → 浏览器先自动压缩到长边 1600px → 上传
- 或者，直接在上面**粘贴一个图片链接**（比如已有图床的地址）

> **图片存在哪里？** 直接存进 PostgreSQL 数据库，通过 `/api/media/...` 提供访问。
> 这是刻意的设计：Vercel 的文件系统是只读的，serverless 环境没法保存上传文件；
> 用数据库可以免去额外申请对象存储服务，备份数据库就等于备份了全部图片。
> 课题组网站的图片量很小，完全够用。

### 关于自动重建

**默认情况下，保存内容后会自动触发一次前端重建**（约 1 分钟后网站上生效），
编辑者不需要记得点任何按钮。

如果想改成手动，把环境变量 `AUTO_REBUILD_ON_SAVE` 设为 `0`，
之后就用列表页右上角的「🚀 重建前台站点」动作来发布。

### 列表页直接改

列表页里可以**直接修改**排序、发布状态、是否精选、是否置顶，改完点右下角保存。

AI 生成新闻摘要需要新闻修改权限；摘要保存成功后也会按自动发布设置触发重建。

### 前台成果检索

科研成果页支持搜索标题、作者、期刊或会议，并组合年份、类型和研究方向筛选。
结果总数和各年份数量会同步更新；点击「清除筛选」恢复全部成果。
成果卡片还支持展开摘要、查看与下载 BibTeX 引用；引用根据已有元数据生成，使用前请核对原文。

后台的作者列表、研究兴趣、关键词和新闻标签均可每行填写一项，无需编辑 JSON。
工作台提供草稿快捷入口和最近 8 条内容更新，显示范围遵循当前账号权限。
本轮开源参考与实现边界见 [项目参考说明](docs/project-references.md)。

### 本地回归验证

```powershell
.venv/Scripts/python.exe api/manage.py test core --settings=labbackend.test_settings
npm test
npm run build
npm run verify:dist
```

测试配置强制使用内存 SQLite，发布请求和 AI 请求在测试中模拟，不连接 `.env.local` 中的业务数据库或触发线上重建。
`npm test` 覆盖 BibTeX 生成、新闻标签筛选与站内搜索排序；`npm run verify:dist` 检查构建产物的站内断链与基础 SEO / 可访问性规范。

---

## 五、部署到 GitHub + Vercel

### 步骤 1：推送代码到 GitHub

```bash
git init
git add .
git commit -m "课题组网站：Astro 前端 + Django 后台"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

### 步骤 2：在 Vercel 导入仓库

1. 打开 <https://vercel.com/new>，选择刚推送的仓库。
2. **Root Directory 保持默认（仓库根目录）**，不要改。
3. Framework Preset 会自动识别为 **Astro**。
4. 先点 **Deploy**（第一次会因为没有数据库而构建失败或显示空内容，属于正常，继续往下做）。

### 步骤 3：创建 PostgreSQL 数据库

在 Vercel 项目页 → **Storage** → **Create Database** → 选 **Postgres**（或接入 Neon / Supabase）。

创建后 Vercel 会**自动注入 `DATABASE_URL`** 到项目环境变量，无需手动复制。

> 连接串建议使用**带连接池**的地址（Neon 的 `-pooler` 后缀、Supabase 的 pooler 端口 6543），
> 因为 Serverless 函数会频繁新建连接。

### 步骤 4：配置环境变量

项目 → **Settings** → **Environment Variables**（Environment 建议三个都勾上）：

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | ✅ | 生产密钥。生成：`python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DATABASE_URL` | ✅ | 上一步自动注入，一般不用手动填 |
| `DJANGO_ALLOWED_HOSTS` | ✅ | 例如 `.vercel.app,lab.example.edu.cn` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | ✅ | 例如 `https://*.vercel.app,https://lab.example.edu.cn` |
| `VERCEL_DEPLOY_HOOK_URL` | 建议 | 后台「重建前台站点」用，见步骤 6 |
| `DEEPSEEK_API_KEY` | 可选 | 只用 AI 生成摘要时才需要 |
| `API_BASE` | 可选 | 前端构建时拉取内容的地址；不填会自动用 Vercel 的域名 |

### 步骤 5：执行数据库迁移

在本地把生产环境变量拉下来，然后对**线上数据库**执行迁移：

```bash
# 关联项目（推荐用 npx，不必全局安装）
npx vercel login
npx vercel link                              # 关联到刚创建的项目
npx vercel env pull .env.local               # 把环境变量拉到本地

python api/manage.py migrate                 # ★ 建表（对线上数据库执行）
python api/manage.py seed_content            # 可选：把现有 Markdown 导入数据库

# ★ 创建管理员账号。不想交互式输入就用下面三个环境变量：
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=you@example.com \
DJANGO_SUPERUSER_PASSWORD='换成你的强密码' \
python api/manage.py createsuperuser --noinput
```

> `migrate` 只建表结构；`seed_content` 会把 `src/content/` 里的示例内容写进数据库。
> 不想用示例内容就跳过它，直接在后台新建。
>
> 注意：`vercel env pull` 会把 `DATABASE_URL` 一并拉到 `.env.local`，
> Django 的 `settings.py` 会自动读取该文件，所以上面几条命令直接操作的就是**线上数据库**。

### 步骤 6：配置自动重建（Deploy Hook）

1. Vercel 项目 → **Settings** → **Git** → **Deploy Hooks** → 新建一个
   （名字随意，Branch 选 `main`），复制生成的 URL。
2. 把它填到环境变量 `VERCEL_DEPLOY_HOOK_URL`。
3. **Redeploy 一次**让变量生效。

之后在后台点「🚀 重建前台站点」，网站就会自动更新。

### 步骤 7：验证

- 前台：`https://<你的项目>.vercel.app/`
- 接口：`https://<你的项目>.vercel.app/api/content/`
- 后台：`https://<你的项目>.vercel.app/api/admin/`

---

## 六、两个必须知道的部署坑

### 1. `vercel.json` 里的 `"framework": "astro"` 不能删

Vercel 会扫描根目录的 `requirements.txt`，一旦识别出 Django，就会启用 **Django 框架预设**，
此时**所有请求都会交给 Django**，Astro 的静态站点就再也访问不到了。

显式声明 `"framework": "astro"` 可以跳过框架自动探测，
从而让 `api/index.py` 作为普通的**文件式函数**只接管 `/api/*`。

### 2. Django Admin 的静态文件挂在 `/api/static/` 下

因为只有 `/api/*` 会转发给 Django 函数，Admin 的 CSS/JS 也必须在这个前缀下才拿得到，
所以 `settings.py` 里写的是：

```python
STATIC_URL = "/api/static/"
WHITENOISE_USE_FINDERS = True   # 直接从已安装的 app 里取文件，无需 collectstatic
```

如果你把 `STATIC_URL` 改回 `/static/`，后台会变成没有样式的裸 HTML 页面。

---

## 七、常见问题

**Q：前台内容没跟着后台更新？**
保存内容后会自动触发重建，等约 1 分钟刷新即可（若把 `AUTO_REBUILD_ON_SAVE` 设成了 0，
则需手动执行「🚀 重建前台站点」动作）。等了还没变化，去 Vercel → Deployments
看最新一次构建是否成功、以及 `VERCEL_DEPLOY_HOOK_URL` 是否已配置。

**Q：`/api/` 下全部 404？**
先访问 `/api/health/`。若也 404，说明请求没进到函数 —— 检查 `vercel.json` 的 `rewrites` 与
`"framework"` 设置；若 `/api/health/` 正常但其它 404，检查 `api/labbackend/urls.py` 的前缀。

**Q：后台登录报 CSRF 错误？**
把 `DJANGO_CSRF_TRUSTED_ORIGINS` 补上你实际访问的域名，**要带 `https://` 协议头**。

**Q：数据库连接报 `too many clients`？**
换用带连接池的连接串，配置里已开启 `DISABLE_SERVER_SIDE_CURSORS` 配合事务级池化。

**Q：首次部署后网站是空的？**
构建时后端还没有数据（或第一次构建时后端尚不可用），此时会自动回退到 `src/content/` 的
Markdown 示例内容。执行 `seed_content` 并在后台点一次「重建前台站点」即可。

**Q：还需要 Pages CMS 吗？**
不需要了。之前的 `.pages.yml` 已移除 —— 现在内容以数据库为准，Markdown 只作为
首次导入的种子数据和接口不可用时的兜底。

**Q：从 Vercel 控制台导入仓库时报「配置错误」/ 连不上仓库？**
Vercel 的 GitHub App 还没拿到你仓库的授权。到
<https://github.com/apps/vercel/installations/new> 安装授权（选中该仓库或 All repositories），
之后 push 就会自动部署了。

**Q：部署保护挡住了构建时的接口请求？**
团队账号默认开启 Deployment Protection，会导致构建时自取 `/api/content/` 被拦。
用 `vercel project protection disable <项目名> --sso` 关闭，或在控制台
Settings → Deployment Protection 里关掉。

**Q：怎么让百度 / Google 收录？**
站点已内置 `/sitemap.xml`（自动枚举全部成员、新闻、成果、方向页面）与 `/robots.txt`，
首页还输出了 `ResearchOrganization` 结构化数据。上线后到
[百度搜索资源平台](https://ziyuan.baidu.com/) 和
[Google Search Console](https://search.google.com/search-console) 提交
`https://你的域名/sitemap.xml` 即可。

**Q：想换配色？**
改 `src/styles/global.css` 顶部的 CSS 变量（`--accent` 是主色），浅色和深色两套各改一次即可。

---

## 八、上线前请替换的占位内容

所有内容目前都是示例数据：

- [ ] 后台「站点设置」：课题组名称、缩写、单位、地址、邮箱、招生信息、页脚链接
- [ ] 后台「研究方向」：5 个示例方向
- [ ] 后台「团队成员」：8 位示例成员
- [ ] 后台「科研新闻」：6 条示例新闻
- [ ] 后台「科研成果」：14 项示例成果
- [ ] `public/favicon.svg` 站点图标
- [ ] `public/images/team/`、`public/images/research/` 真实图片

---

## 九、License

站点与后端代码可自由使用与修改。示例文字与配图仅供占位，请替换为课题组自有内容。
