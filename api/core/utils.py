"""通用工具：Markdown 渲染、触发前端重建。"""

import json
import logging
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import markdown as _markdown
except ImportError:  # pragma: no cover - 依赖缺失时降级为纯文本
    _markdown = None


def render_markdown(text: str) -> str:
    """把 Markdown 渲染成 HTML，供前端直接注入。"""
    if not text:
        return ""
    if _markdown is None:
        return f"<p>{text}</p>"
    return _markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html",
    )


def as_list(value) -> list:
    """容错：把 JSONField 的值统一成 list。"""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return []


def as_dict(value) -> dict:
    """容错：把 JSONField 的值统一成 dict，并丢弃空值。"""
    if isinstance(value, dict):
        return {k: v for k, v in value.items() if v}
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def trigger_deploy() -> tuple[bool, str]:
    """调用 Vercel Deploy Hook，重新构建前端静态站点。"""
    url = getattr(settings, "VERCEL_DEPLOY_HOOK_URL", "")
    if not url:
        return False, "未配置 VERCEL_DEPLOY_HOOK_URL，已跳过站点重建。"

    try:
        request = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                return True, "已触发站点重建，约 1 分钟后前台生效。"
            return False, f"Deploy Hook 返回状态码 {response.status}。"
    except Exception as exc:  # noqa: BLE001 - 后台操作不应因网络问题中断
        logger.exception("触发 Vercel 重建失败")
        return False, f"触发重建失败：{exc}"
