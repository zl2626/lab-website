"""后台表单自定义字段：既能直接上传图片，也能粘贴图片链接。

Django 自带的 ImageField 需要可写的文件系统，serverless 环境用不了；
这里把上传的文件交给 media.save_uploaded_image 存进数据库，
最终在字段里保存的仍然是一个普通 URL 字符串 —— 所以模型层不需要改动。
"""

from __future__ import annotations

from django import forms
from django.core.files.uploadedfile import UploadedFile

from .media import MediaError, save_uploaded_image

PREVIEW_PREFIXES = ("http://", "https://", "/api/media/", "/images/")


class ImageOrUrlWidget(forms.TextInput):
    template_name = "core/widgets/image_or_url.html"

    class Media:
        css = {"all": ("core/css/lab-admin.css",)}
        js = ("core/js/image-upload.js",)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        preview = ""
        if isinstance(value, str) and value.startswith(PREVIEW_PREFIXES):
            preview = value
        context["widget"]["preview_url"] = preview
        context["widget"]["upload_name"] = f"{name}__upload"
        return context

    def value_from_datadict(self, data, files, name):
        # 优先使用「新上传的文件」，其次才用文本框里的链接
        upload = files.get(f"{name}__upload") if files else None
        if upload is not None and getattr(upload, "size", 0):
            return upload
        return data.get(name, "")


class ImageOrUrlField(forms.CharField):
    """存的是 URL 字符串；如果用户上传了文件，先落库再返回其访问地址。"""

    widget = ImageOrUrlWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("max_length", 300)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if isinstance(value, UploadedFile):
            if not value.size:
                return ""
            try:
                return save_uploaded_image(value)
            except MediaError as exc:
                raise forms.ValidationError(str(exc)) from exc
        return super().clean(value)
