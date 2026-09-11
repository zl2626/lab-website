"""图片存储 —— 直接把文件存进数据库，不依赖任何外部对象存储。

为什么这么做：
    Vercel 的文件系统是只读的，serverless 环境没法把用户上传的图片写进磁盘。
    常规做法是接 S3 / Vercel Blob，但那需要额外申请一个存储服务。
    课题组网站的图片量很小（成员照片、封面图），直接存进 PostgreSQL 完全够用，
    而且零外部依赖、备份数据库就等于备份了图片。

访问路径：/api/media/<name>，由 views.media 提供，带一年强缓存。
"""

from __future__ import annotations

import hashlib
import io
import mimetypes
import os
from datetime import date

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from .models import MediaFile

# 上传限制
MAX_UPLOAD_BYTES = 4 * 1024 * 1024  # Vercel 请求体上限约 4.5MB，这里留点余量
MAX_DIMENSION = 1600  # 长边超过这个值会自动等比缩小
JPEG_QUALITY = 85

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

try:  # Pillow 没有也能跑（只是不做压缩校验）
    from PIL import Image, ImageOps

    HAS_PILLOW = True
except ImportError:  # pragma: no cover
    HAS_PILLOW = False


class MediaError(ValueError):
    """上传的图片不合法。"""


def _process(raw: bytes, filename: str) -> tuple[bytes, str, str, int, int]:
    """压缩并规整图片。返回 (数据, 扩展名, MIME, 宽, 高)。"""
    ext = os.path.splitext(filename or "")[1].lower()
    guessed = mimetypes.guess_type(filename or "")[0] or "image/jpeg"

    if not HAS_PILLOW:
        if ext not in ALLOWED_EXTENSIONS:
            raise MediaError("只支持 JPG / PNG / WebP / GIF 图片。")
        if len(raw) > MAX_UPLOAD_BYTES:
            raise MediaError("图片太大了，请压缩到 4MB 以内。")
        return raw, ext or ".jpg", guessed, 0, 0

    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception as exc:  # noqa: BLE001
        raise MediaError("这个文件不是有效的图片。") from exc

    # 手机竖拍的照片经常带旋转信息，先按 EXIF 摆正
    try:
        image = ImageOps.exif_transpose(image) or image
    except Exception:  # noqa: BLE001
        pass

    width, height = image.size

    # 等比缩小
    if max(width, height) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / float(max(width, height))
        width = max(1, int(width * ratio))
        height = max(1, int(height * ratio))
        image = image.resize((width, height), Image.LANCZOS)

    has_alpha = image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )

    buffer = io.BytesIO()
    if has_alpha:
        image.convert("RGBA").save(buffer, format="PNG", optimize=True)
        out_ext, mime = ".png", "image/png"
    else:
        image.convert("RGB").save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        out_ext, mime = ".jpg", "image/jpeg"

    data = buffer.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        raise MediaError("图片压缩后仍然过大，请换一张尺寸更小的图片。")

    return data, out_ext, mime, width, height


def save_uploaded_image(upload) -> str:
    """保存上传的图片，返回可访问的 URL 路径。"""
    raw = upload.read()
    if not raw:
        raise MediaError("没有读取到文件内容。")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise MediaError(
            f"图片超过 {MAX_UPLOAD_BYTES // 1024 // 1024}MB，请先压缩再上传。"
        )

    data, ext, mime, width, height = _process(raw, getattr(upload, "name", ""))

    # 用内容哈希命名：内容不变则文件名不变，可以放心用一年强缓存
    digest = hashlib.sha1(data).hexdigest()[:16]
    today = date.today()
    name = f"images/{today:%Y/%m}/{digest}{ext}"

    MediaFile.objects.update_or_create(
        name=name,
        defaults={
            "content_type": mime,
            "size": len(data),
            "width": width,
            "height": height,
            "data": data,
        },
    )
    return f"{settings.MEDIA_URL}{name}"


@deconstructible
class DatabaseStorage(Storage):
    """把文件存进数据库的 Django Storage 后端。"""

    def _open(self, name, mode="rb"):
        record = MediaFile.objects.get(name=name)
        return ContentFile(bytes(record.data), name=name)

    def _save(self, name, content):
        data = content.read()
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        MediaFile.objects.update_or_create(
            name=name,
            defaults={"content_type": mime, "size": len(data), "data": data},
        )
        return name

    def exists(self, name) -> bool:
        return MediaFile.objects.filter(name=name).exists()

    def delete(self, name) -> None:
        MediaFile.objects.filter(name=name).delete()

    def size(self, name) -> int:
        record = MediaFile.objects.filter(name=name).first()
        return record.size if record else 0

    def url(self, name) -> str:
        return f"{settings.MEDIA_URL}{name}"

    def get_accessed_time(self, name):  # pragma: no cover - 不需要
        raise NotImplementedError

    def get_created_time(self, name):  # pragma: no cover - 不需要
        raise NotImplementedError

    def get_modified_time(self, name):  # pragma: no cover - 不需要
        raise NotImplementedError
