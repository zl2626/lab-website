"""Editor-friendly inputs that preserve the existing JSON storage format."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from django import forms
from django.core.validators import URLValidator

PAGE_COPY = json.loads(Path(__file__).with_name("page_copy.json").read_text(encoding="utf-8"))


def validate_link(value):
    if any(char.isspace() or ord(char) < 32 for char in value):
        raise forms.ValidationError("链接不能包含空格或换行，请使用编码后的完整地址。")
    if value.startswith("/") and not value.startswith("//") and "\\" not in value:
        return
    if urlsplit(value).scheme not in ("http", "https"):
        raise forms.ValidationError("链接须为 / 开头的站内路径或完整的 http(s) 地址。")
    URLValidator(schemes=["http", "https"])(value)


class LinkListField(forms.Field):
    widget = forms.Textarea(attrs={"rows": 6, "cols": 70})

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("help_text", "每行：名称 | 链接。兼容原有 JSON 数组；站内链接以 / 开头。")
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list):
            return "\n".join(f"{item.get('label', '')} | {item.get('href', '')}" for item in value if isinstance(item, dict))
        return value

    def to_python(self, value):
        if value in self.empty_values:
            return []
        if isinstance(value, str):
            if value.strip().startswith("["):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError as exc:
                    raise forms.ValidationError("链接 JSON 格式有误。") from exc
            else:
                entries = []
                for line in value.splitlines():
                    if not line.strip():
                        continue
                    label, separator, href = line.partition("|")
                    if not separator:
                        raise forms.ValidationError("每行请用 | 分隔名称和链接。")
                    entries.append({"label": label.strip(), "href": href.strip()})
                value = entries
        if not isinstance(value, list):
            raise forms.ValidationError("请填写链接列表。")
        for item in value:
            if not isinstance(item, dict) or not isinstance(item.get("label"), str) or not item["label"].strip() or not isinstance(item.get("href"), str):
                raise forms.ValidationError("每条链接必须包含名称和地址。")
            validate_link(item["href"])
        return value


class MemberLinksField(LinkListField):
    def prepare_value(self, value):
        if isinstance(value, dict):
            return "\n".join(f"{key} | {url}" for key, url in value.items())
        return value

    def to_python(self, value):
        if isinstance(value, str) and value.strip().startswith("{"):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError("链接 JSON 格式有误。") from exc
        if isinstance(value, dict):
            value = [{"label": key, "href": url} for key, url in value.items()]
        entries = super().to_python(value)
        allowed = {"homepage", "scholar", "github", "dblp", "orcid"}
        if any(item["label"] not in allowed for item in entries):
            raise forms.ValidationError("名称请使用 homepage、scholar、github、dblp 或 orcid。")
        if len({item["label"] for item in entries}) != len(entries):
            raise forms.ValidationError("同一种链接只能填写一次。")
        return {item["label"]: item["href"] for item in entries}


class LineListField(forms.Field):
    widget = forms.Textarea(attrs={"rows": 4, "cols": 60})

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("help_text", "每行填写一项，无需填写 JSON；也兼容已有 JSON 数组。")
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return value

    def to_python(self, value):
        if value in self.empty_values:
            return []
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError as exc:
                    raise forms.ValidationError("JSON 数组格式有误，也可以改为每行一项。") from exc
            else:
                value = value.splitlines()
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise forms.ValidationError("请填写文本列表，每行一项。")
        return [item.strip() for item in value if item.strip()]
