"""
Django 配置 —— 同时适用于本地开发与 Vercel Serverless。

环境变量（在 Vercel 项目里配置，本地写进 .env.local）：
  DATABASE_URL          PostgreSQL 连接串，Vercel 绑定 Postgres 后会自动注入
  DJANGO_SECRET_KEY     生产环境必须设置，否则用不安全的默认值
  DJANGO_DEBUG          设为 1 开启调试，生产环境不要设置
  DJANGO_ALLOWED_HOSTS  逗号分隔，默认 *
  DEEPSEEK_API_KEY      预留给 AI 辅助功能
  VERCEL_DEPLOY_HOOK_URL 后台保存后自动触发前端重建用的 Deploy Hook
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# api/ 目录（Django 项目所在）
BASE_DIR = Path(__file__).resolve().parent.parent
# 仓库根目录（Astro 前端 + src/content 都在这）
ROOT_DIR = BASE_DIR.parent

# 本地开发时从仓库根的 .env.local 读环境变量（该文件不入库）
load_dotenv(ROOT_DIR / ".env.local")
load_dotenv(ROOT_DIR / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def env_list(key: str, default: str = "") -> list[str]:
    raw = env(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------------
# 安全
# --------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY") or (
    # 本地开发兜底；生产环境必须通过 DJANGO_SECRET_KEY 覆盖
    "django-insecure-local-dev-only-key-do-not-use-in-production"
)
if not DEBUG and not env("DJANGO_SECRET_KEY"):
    # 不抛异常，避免首次部署因漏配变量直接 500；只做提示
    import warnings

    warnings.warn("警告：未设置 DJANGO_SECRET_KEY，正在使用不安全的默认密钥。", stacklevel=1)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*") or ["*"]

# Vercel 部署在代理后面，需要信任转发头
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://*.vercel.app",
)

# 生产环境走 https，Cookie 加 Secure
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"

# --------------------------------------------------------------------------
# 应用
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "core.admin_site.LabAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise 负责在 serverless 环境里提供 admin 的 CSS/JS（见下方 STATIC 配置）
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "labbackend.urls"
WSGI_APPLICATION = "labbackend.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------
# 数据库
# --------------------------------------------------------------------------
DATABASE_URL = env("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,  # serverless 下不要复用连接
            conn_health_checks=False,
            ssl_require=True,
        )
    }
    # 使用 PgBouncer 等事务级连接池时必须开启
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    # 本地开发 / 未配置数据库时用 SQLite，保证项目一定能跑起来。
    # 特意放在仓库根目录（而不是 api/ 里）：这样 Vercel 打包函数时
    # 不会把本地数据库文件带上去。
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ROOT_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# 静态文件（Django Admin 的样式与脚本）
# --------------------------------------------------------------------------
# 关键点：函数只接管 /api/*，所以静态文件也必须挂在 /api/ 前缀下，
# 才能同时被 WhiteNoise 与 vercel.json 的 /api/(.*) 重写规则命中。
STATIC_URL = "/api/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# 用 finders 直接从已安装的 app（含 django.contrib.admin）里取文件，
# 这样 serverless 环境无需执行 collectstatic。
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

STORAGES = {
    # 用户上传的图片直接存进数据库，见 core/media.py（serverless 无可用文件系统）
    "default": {"BACKEND": "core.media.DatabaseStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# --------------------------------------------------------------------------
# 用户上传的图片（成员照片、封面等）
# --------------------------------------------------------------------------
# 同样挂在 /api/ 前缀下，才能被 WhiteNoise / 函数路由命中
MEDIA_URL = "/api/media/"
MEDIA_ROOT = BASE_DIR / "media"  # 仅占位，实际读写都由 DatabaseStorage 接管

# Vercel 请求体上限约 4.5MB，这里留一点余量
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000

# --------------------------------------------------------------------------
# 其它
# --------------------------------------------------------------------------
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

LOGIN_URL = "/api/admin/login/"

# 预留给后续 AI 功能（例如自动生成新闻摘要）
DEEPSEEK_API_KEY = env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = env("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = env("DEEPSEEK_MODEL", "deepseek-chat")

# 后台保存内容后，用它自动触发 Vercel 重新构建前端
# 方式一：Deploy Hook（要求项目已连接 Git 仓库）
VERCEL_DEPLOY_HOOK_URL = env("VERCEL_DEPLOY_HOOK_URL")

# 方式二：Vercel REST API 重新部署（项目未连接 Git 仓库时用这个）
#   VERCEL_API_TOKEN   Vercel 账号令牌，建议用 `vercel tokens add` 建一个专用令牌
#   VERCEL_PROJECT_ID  项目 ID（prj_ 开头），在项目 Settings 里可以看到
#   VERCEL_TEAM_ID     团队 ID（team_ 开头），个人账号可留空
VERCEL_API_TOKEN = env("VERCEL_API_TOKEN")
VERCEL_PROJECT_ID = env("VERCEL_PROJECT_ID")
VERCEL_TEAM_ID = env("VERCEL_TEAM_ID")

# 默认在保存内容后自动触发一次前端重建，这样编辑者不需要记得点「重建」按钮。
# 如果想改成手动，设 AUTO_REBUILD_ON_SAVE=0。
AUTO_REBUILD_ON_SAVE = env_bool("AUTO_REBUILD_ON_SAVE", True)

# 前端站点地址（用于 API 里返回绝对链接，可留空）
SITE_BASE_URL = env("SITE_BASE_URL")
