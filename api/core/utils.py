"""通用工具：Markdown 渲染、触发前端重建。"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

VERCEL_API_BASE = "https://api.vercel.com"

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


def _post_deploy_hook(url: str) -> tuple[bool, str]:
    """方式一：调用 Vercel Deploy Hook（需要项目已连接 Git 仓库）。"""
    try:
        request = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                return True, "已触发站点重建，约 1 分钟后前台生效。"
            return False, f"Deploy Hook 返回状态码 {response.status}。"
    except Exception as exc:  # noqa: BLE001 - 后台操作不应因网络问题中断
        logger.exception("触发 Vercel 重建失败")
        return False, f"触发重建失败：{exc}"


def _vercel_api_request(url: str, *, token: str, method: str = "GET", payload: dict | None = None):
    """带鉴权地调用 Vercel REST API，返回解析后的 JSON。"""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8") or "{}"
        return json.loads(raw)


def _post_deploy_api(token: str, project_id: str, team_id: str = "") -> tuple[bool, str]:
    """方式二：用 Vercel REST API 重新部署一次线上版本。

    适合「项目没有连接 Git 仓库」的情况 —— 这类项目无法创建 Deploy Hook。
    原理是取最近一次生产部署作为源，重新构建一份，生产域名会自动指过去。
    """
    query = {"projectId": project_id, "target": "production", "limit": "1"}
    if team_id:
        query["teamId"] = team_id
    list_url = f"{VERCEL_API_BASE}/v6/deployments?{urllib.parse.urlencode(query)}"

    try:
        payload = _vercel_api_request(list_url, token=token)
    except urllib.error.HTTPError as exc:
        return False, f"读取历史部署失败（HTTP {exc.code}），请检查 VERCEL_API_TOKEN 是否有权限。"
    except Exception as exc:  # noqa: BLE001
        logger.exception("读取 Vercel 历史部署失败")
        return False, f"读取历史部署失败：{exc}"

    deployments = payload.get("deployments") or []
    if not deployments:
        return False, "没有找到可用于重建的历史部署，请先手动部署一次。"

    source = deployments[0]
    body = {
        "name": source.get("name") or project_id,
        "target": "production",
        "deploymentId": source["uid"],
    }
    create_query = {"forceNew": "1"}
    if team_id:
        create_query["teamId"] = team_id
    create_url = f"{VERCEL_API_BASE}/v13/deployments?{urllib.parse.urlencode(create_query)}"

    try:
        created = _vercel_api_request(create_url, token=token, method="POST", payload=body)
    except urllib.error.HTTPError as exc:
        return False, f"请求重建失败（HTTP {exc.code}），请检查 VERCEL_API_TOKEN 的权限范围。"
    except Exception as exc:  # noqa: BLE001
        logger.exception("请求 Vercel 重建失败")
        return False, f"请求重建失败：{exc}"

    url = created.get("url") or ""
    return True, f"已请求站点重建，约 1 分钟后前台生效。（{url}）"


def trigger_deploy() -> tuple[bool, str]:
    """触发一次前端重建。

    优先用 Deploy Hook；没有配置时回退到 Vercel REST API，
    这样「没有连接 Git 仓库」的项目也能让后台改完就上线。
    """
    hook_url = getattr(settings, "VERCEL_DEPLOY_HOOK_URL", "")
    if hook_url:
        return _post_deploy_hook(hook_url)

    token = getattr(settings, "VERCEL_API_TOKEN", "")
    project_id = getattr(settings, "VERCEL_PROJECT_ID", "")
    if token and project_id:
        return _post_deploy_api(token, project_id, getattr(settings, "VERCEL_TEAM_ID", ""))

    return False, "未配置发布服务，内容已保存但不会同步到官网。"


def deploy_configured() -> bool:
    """是否已经配置了任意一种发布方式。"""
    if getattr(settings, "VERCEL_DEPLOY_HOOK_URL", ""):
        return True
    return bool(getattr(settings, "VERCEL_API_TOKEN", "") and getattr(settings, "VERCEL_PROJECT_ID", ""))
