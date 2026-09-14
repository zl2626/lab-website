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
