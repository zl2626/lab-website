"""DeepSeek API 封装（可选功能）。

配置了 DEEPSEEK_API_KEY 后，后台可用「AI 生成摘要」动作。
没配置也不会影响任何其它功能。
"""

import json
import urllib.error
import urllib.request

from django.conf import settings


class AIError(RuntimeError):
    """调用大模型失败。"""


def _chat(messages: list[dict], temperature: float = 0.3, timeout: int = 40) -> str:
    api_key = getattr(settings, "DEEPSEEK_API_KEY", "")
    if not api_key:
        raise AIError("未配置 DEEPSEEK_API_KEY，请在 Vercel 环境变量中添加。")

    base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")

    body = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise AIError(f"DeepSeek 返回 {exc.code}：{detail}") from exc
    except Exception as exc:  # noqa: BLE001
        raise AIError(f"调用 DeepSeek 失败：{exc}") from exc

    try:
        return payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise AIError("DeepSeek 返回格式异常。") from exc


def generate_summary(title: str, body: str, limit: int = 100) -> str:
    """根据正文生成一句不超过 limit 字的中文摘要。"""
    prompt = (
        "你是学术课题组的网站编辑。请把下面这条科研新闻概括成一句"
        f"不超过 {limit} 字的中文摘要，直接输出摘要本身，不要任何前缀、引号或解释。\n\n"
        f"标题：{title}\n\n正文：\n{body[:3000]}"
    )
    return _chat([{"role": "user", "content": prompt}])
