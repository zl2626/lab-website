"""
Vercel Serverless 函数入口。

Vercel 会加载本模块顶层名为 `app` 的 WSGI 可调用对象，
所有命中 /api/* 的请求都会交给 Django 处理。

注意：Vercel 会把浏览器访问的原始路径原样放进 WSGI 的 PATH_INFO
（例如 /api/news/），所以 Django 的 URLconf 也挂在 /api/ 前缀下。
"""

import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labbackend.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

_wsgi_app = get_wsgi_application()

API_PREFIX = "/api"


def app(environ, start_response):  # noqa: ANN001, ANN201
    """把请求交给 Django，并保证 PATH_INFO 一定以 /api 开头。"""
    path = environ.get("PATH_INFO") or "/"

    if path in ("/api/index", "/api/index.py"):
        # 兜底：如果 Vercel 传进来的是函数自身路径而不是原始路径
        path = "/api/"
    elif not path.startswith(API_PREFIX):
        path = API_PREFIX + (path if path.startswith("/") else "/" + path)

    environ["PATH_INFO"] = path
    environ["SCRIPT_NAME"] = ""
    return _wsgi_app(environ, start_response)
