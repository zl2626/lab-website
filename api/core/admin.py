"""Django Admin —— 管理员日常维护内容的后台。

访问地址：https://<你的域名>/api/admin/

设计取向：
  * 照片 / 封面支持「直接上传」或「粘贴链接」两种方式，上传的图片会自动压缩后存进数据库；
  * 保存内容后自动触发一次前端重建（可用环境变量 AUTO_REBUILD_ON_SAVE=0 关掉），
    避免“改了内容却没生效”的困惑。
"""

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db import transaction
from django.utils.html import format_html

from .ai import AIError, generate_summary
from .forms import LineListField, LinkListField, MemberLinksField, PAGE_COPY
from .models import MediaFile, Member, News, Publication, ResearchArea, SiteSetting, RobotProject
from .utils import trigger_deploy
from .widgets import ImageOrUrlField


# ---------------------------------------------------------------------------
# 通用动作 / 逻辑
# ---------------------------------------------------------------------------
@admin.action(description="🚀 重建前台站点（让本次修改在网站上生效）", permissions=["publish"])
def rebuild_site(modeladmin, request, queryset):
    ok, message = trigger_deploy()
    modeladmin.message_user(request, message, messages.SUCCESS if ok else messages.WARNING)


@admin.action(description="🤖 用 AI 根据正文生成摘要", permissions=["change"])
def ai_make_summary(modeladmin, request, queryset):
    success, failures = 0, []
    for obj in queryset:
        try:
            obj.summary = generate_summary(obj.title, obj.body or obj.summary or "")
            obj.save(update_fields=["summary", "updated_at"])
            success += 1
        except AIError as exc:
            failures.append(f"{obj.title}：{exc}")

    if success:
        modeladmin.message_user(request, f"已为 {success} 条新闻生成摘要。", messages.SUCCESS)
        schedule_rebuild(request, modeladmin)
    for note in failures:
        modeladmin.message_user(request, note, messages.ERROR)


def schedule_rebuild(request, modeladmin):
    """一次请求内只触发一次重建，避免列表页批量编辑时重复构建。"""
    if not getattr(settings, "AUTO_REBUILD_ON_SAVE", True):
        return
    if getattr(request, "_lab_rebuild_scheduled", False):
        return
    request._lab_rebuild_scheduled = True

    def run():
        ok, message = trigger_deploy()
        if ok:
            modeladmin.message_user(request, message, messages.SUCCESS)
        else:
            modeladmin.message_user(request, message, messages.WARNING)

    # 等事务提交后再触发，避免前端构建时读到旧数据
    transaction.on_commit(run)


class AutoRebuildMixin:
    """保存或删除后自动重建前台站点。"""

    def has_publish_permission(self, request):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        schedule_rebuild(request, self)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        schedule_rebuild(request, self)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        schedule_rebuild(request, self)


# ---------------------------------------------------------------------------
# 表单：图片字段既支持上传，也支持粘贴链接
# ---------------------------------------------------------------------------
class ResearchAreaForm(forms.ModelForm):
    cover = ImageOrUrlField(label="配图")
    keywords = LineListField(label="关键词")

    class Meta:
        model = ResearchArea
        fields = "__all__"


class MemberForm(forms.ModelForm):
    photo = ImageOrUrlField(label="照片")
    interests = LineListField(label="研究兴趣")
    hobbies = LineListField(label="兴趣爱好")
    areas = LineListField(
        label="所属研究方向",
        help_text="每行填一个「研究方向」的中文标题，需与研究方向页的标题完全一致，才会在该方向详情页列出此人。",
    )
    links = MemberLinksField(label="相关链接", help_text="每行：homepage | https://…；支持 homepage、scholar、github、dblp、orcid。")

    class Meta:
        model = Member
        fields = "__all__"


class NewsForm(forms.ModelForm):
    cover = ImageOrUrlField(label="封面图")
    tags = LineListField(label="标签")

    class Meta:
        model = News
        fields = "__all__"


class PublicationForm(forms.ModelForm):
    authors = LineListField(label="作者列表", help_text="每行一位作者，顺序即署名顺序；姓名中的逗号会保留。")

    class Meta:
        model = Publication
        fields = "__all__"


class SiteSettingForm(forms.ModelForm):
    group_photo = ImageOrUrlField(label="首页团队合照")
    nav = LinkListField(label="导航菜单", help_text="每行：名称 | 链接。留空使用默认导航。")
    social = LinkListField(label="页脚链接")
    openings_details = forms.CharField(
        label="招生详情（Markdown）",
        required=False,
        widget=forms.Textarea(attrs={"rows": 10, "cols": 80}),
        help_text="可写申请材料清单、申请流程、常见问题。支持 Markdown：# 小标题、- 列表、**加粗**、[链接](https://…)",
    )
    for key, spec in PAGE_COPY.items():
        locals()[f"copy_{key}"] = (forms.URLField if spec["type"] == "url" else forms.CharField)(
            label=spec["label"], required=False,
            widget=forms.Textarea(attrs={"rows": 2, "cols": 70}) if "intro" in key or key.endswith("text") else forms.TextInput(attrs={"size": 70}),
            help_text="支持 {count}，自动替换为当前内容数量。" if "{count}" in spec["default"] else "",
        )

    class Meta:
        model = SiteSetting
        exclude = ("page_copy",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        saved = self.instance.page_copy or {}
        for key, spec in PAGE_COPY.items():
            self.initial[f"copy_{key}"] = saved.get(key, spec["default"])

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.page_copy = {key: self.cleaned_data[f"copy_{key}"] for key in PAGE_COPY}
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# ---------------------------------------------------------------------------
# ModelAdmin
# ---------------------------------------------------------------------------
@admin.register(ResearchArea)
class ResearchAreaAdmin(AutoRebuildMixin, admin.ModelAdmin):
    form = ResearchAreaForm
    list_display = ("title", "title_en", "order", "published", "updated_at")
    list_editable = ("order", "published")
    search_fields = ("title", "title_en", "summary", "slug")
    list_filter = ("published",)
    actions = [rebuild_site]
    fieldsets = (
        ("基本信息", {"fields": ("title", "title_en", "slug", "summary", "icon")}),
        ("展示", {"fields": ("keywords", "order", "cover")}),
        ("正文（支持 Markdown）", {"fields": ("body",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(Member)
class MemberAdmin(AutoRebuildMixin, admin.ModelAdmin):
    form = MemberForm
    list_display = ("name", "role", "title", "order", "published")
    list_editable = ("order", "published")
    list_filter = ("role", "published")
    search_fields = ("name", "name_en", "slug", "email")
    actions = [rebuild_site]
    fieldsets = (
        ("基本信息", {"fields": ("name", "name_en", "slug", "role", "title", "join_year", "now_at")}),
        (
            "照片",
            {
                "fields": ("photo",),
                "description": "点「选择图片…」直接上传，也可以在上面粘贴图片链接。建议用正方形照片（会自动压缩）。",
            },
        ),
        ("联系方式", {"fields": ("email", "links")}),
        ("展示", {"fields": ("areas", "research_focus", "interests", "hobbies", "achievement_summary", "order")}),
        ("个人简介（支持 Markdown）", {"fields": ("bio",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(News)
class NewsAdmin(AutoRebuildMixin, admin.ModelAdmin):
    form = NewsForm
    list_display = ("title", "date", "pinned", "published", "updated_at")
    list_editable = ("pinned", "published")
    list_filter = ("pinned", "published")
    search_fields = ("title", "summary", "slug")
    date_hierarchy = "date"
    actions = [rebuild_site, ai_make_summary]
    fieldsets = (
        ("基本信息", {"fields": ("title", "slug", "date")}),
        ("展示", {"fields": ("summary", "tags", "cover", "pinned")}),
        ("正文（支持 Markdown）", {"fields": ("body",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(Publication)
class PublicationAdmin(AutoRebuildMixin, admin.ModelAdmin):
    form = PublicationForm
    list_display = ("title", "year", "venue_short", "type", "area", "highlight", "published")
    list_editable = ("highlight", "published")
    list_filter = ("year", "type", "highlight", "published")
    search_fields = ("title", "venue", "venue_short", "area", "slug")
    actions = [rebuild_site]
    fieldsets = (
        ("成果信息", {"fields": ("title", "slug", "authors", "year", "type")}),
        ("发表载体", {"fields": ("venue", "venue_short", "area")}),
        ("链接", {"fields": ("link", "pdf", "code")}),
        ("简介与展示", {"fields": ("abstract", "highlight")}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(RobotProject)
class RobotProjectAdmin(AutoRebuildMixin, admin.ModelAdmin):
    list_display = ("name", "research_focus", "model_format", "published", "updated_at")
    list_editable = ("published",)
    list_filter = ("published", "model_format")
    search_fields = ("name", "summary", "research_focus", "slug")
    actions = [rebuild_site]
    fieldsets = (
        ("项目基本信息", {"fields": ("name", "slug", "summary", "research_focus", "order")}),
        ("文件和演示", {"fields": ("model_url", "model_format", "demo_url"), "description": "填写模型或视频的公开地址。建议使用对象存储、GitHub Releases 或网盘链接；大文件不建议直接放进网站服务器。"}),
        ("详细说明", {"fields": ("body",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(SiteSetting)
class SiteSettingAdmin(AutoRebuildMixin, admin.ModelAdmin):
    form = SiteSettingForm
    actions = [rebuild_site]
    list_display = ("name", "abbr", "email", "updated_at")

    fieldsets = (
        ("课题组信息", {"fields": ("name", "name_en", "abbr", "tagline", "affiliation", "description", "group_photo")}),
        ("联系方式", {"fields": ("address", "postcode", "email", "phone")}),
        ("招生信息", {"fields": ("openings_enabled", "openings_title", "openings_text", "openings_details", "openings_email")}),
        (
            "导航与页脚",
            {
                "fields": ("nav", "social", "icp"),
                "description": "每行填写名称 | 链接；导航留空则使用默认菜单。",
            },
        ),
    )

    fieldsets += tuple(
        (group, {"fields": tuple(f"copy_{key}" for key, spec in PAGE_COPY.items() if spec["group"] == group), "classes": ("collapse",)})
        for group in dict.fromkeys(spec["group"] for spec in PAGE_COPY.values())
    )

    def has_add_permission(self, request):
        # 单例：只允许存在一条记录
        return super().has_add_permission(request) and not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # 只有一条记录时直接进编辑页
        if SiteSetting.objects.count() == 1 and not request.GET:
            from django.shortcuts import redirect

            obj = SiteSetting.objects.first()
            return redirect("admin:core_sitesetting_change", obj.pk)
        return super().changelist_view(request, extra_context)


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    """已上传的图片。这里只用于查看和清理，新增统一通过内容表单完成。"""

    list_display = ("thumb", "name", "size_kb", "dimensions", "uploaded_at")
    list_display_links = ("name",)
    search_fields = ("name",)
    ordering = ("-uploaded_at",)
    fields = ("thumb", "name", "content_type", "size_kb", "dimensions", "uploaded_at")
    readonly_fields = fields

    @admin.display(description="预览")
    def thumb(self, obj):
        return format_html(
            '<img src="{}{}" style="height:60px;border-radius:6px;border:1px solid #ddd">',
            settings.MEDIA_URL,
            obj.name,
        )

    @admin.display(description="尺寸")
    def dimensions(self, obj):
        if obj.width and obj.height:
            return f"{obj.width} × {obj.height}"
        return "—"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
