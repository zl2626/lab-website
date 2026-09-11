# 课题组网站

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

登录 `/api/admin/` 后可见 5 个菜单：

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
