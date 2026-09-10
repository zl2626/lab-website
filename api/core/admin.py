"""Django Admin —— 管理员日常维护内容的后台。

访问地址：https://<你的域名>/api/admin/
"""

from django.contrib import admin, messages

from .ai import AIError, generate_summary
from .models import Member, News, Publication, ResearchArea, SiteSetting
from .utils import trigger_deploy


@admin.action(description="🚀 重建前台站点（让本次修改在网站上生效）")
def rebuild_site(modeladmin, request, queryset):
    ok, message = trigger_deploy()
    modeladmin.message_user(request, message, messages.SUCCESS if ok else messages.WARNING)


@admin.action(description="🤖 用 AI 根据正文生成摘要")
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
        modeladmin.message_user(
            request,
            "记得再执行一次「重建前台站点」动作让摘要生效。",
            messages.INFO,
        )
    for note in failures:
        modeladmin.message_user(request, note, messages.ERROR)


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    list_display = ("title", "title_en", "order", "published", "updated_at")
    list_editable = ("order", "published")
    search_fields = ("title", "title_en", "summary", "slug")
    list_filter = ("published",)
    actions = [rebuild_site]
    fieldsets = (
        ("基本信息", {"fields": ("title", "title_en", "slug", "summary", "icon")}),
        ("展示", {"fields": ("keywords", "order", "cover")}),
        ("正文", {"fields": ("body",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("name", "name_en", "role", "title", "order", "published")
    list_editable = ("order", "published")
    list_filter = ("role", "published")
    search_fields = ("name", "name_en", "slug", "email")
    actions = [rebuild_site]
    fieldsets = (
        ("基本信息", {"fields": ("name", "name_en", "slug", "role", "title", "join_year")}),
        ("联系方式", {"fields": ("email", "links")}),
        ("展示", {"fields": ("photo", "interests", "order")}),
        ("个人简介", {"fields": ("bio",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "pinned", "published", "updated_at")
    list_editable = ("pinned", "published")
    list_filter = ("pinned", "published")
    search_fields = ("title", "summary", "slug")
    date_hierarchy = "date"
    actions = [rebuild_site, ai_make_summary]
    fieldsets = (
        ("基本信息", {"fields": ("title", "slug", "date")}),
        ("展示", {"fields": ("summary", "tags", "cover", "pinned")}),
        ("正文", {"fields": ("body",)}),
        ("发布", {"fields": ("published",)}),
    )


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
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


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    actions = [rebuild_site]
    list_display = ("name", "abbr", "email", "updated_at")

    fieldsets = (
        ("课题组信息", {"fields": ("name", "name_en", "abbr", "tagline", "affiliation", "description")}),
        ("联系方式", {"fields": ("address", "postcode", "email", "phone")}),
        ("招生信息", {"fields": ("openings_enabled", "openings_title", "openings_text", "openings_email")}),
        (
            "导航与页脚",
            {
                "fields": ("nav", "social", "icp"),
                "description": "nav 留空则使用默认菜单；格式示例：[{\"label\": \"首页\", \"href\": \"/\"}]",
            },
        ),
    )

    def has_add_permission(self, request):
        # 单例：只允许存在一条记录
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # 只有一条记录时直接进编辑页
        if SiteSetting.objects.count() == 1 and not request.GET:
            obj = SiteSetting.objects.first()
            from django.shortcuts import redirect

            return redirect("admin:core_sitesetting_change", obj.pk)
        return super().changelist_view(request, extra_context)

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        if "_continue" not in request.POST and "_addanother" not in request.POST:
            self.message_user(
                request,
                "已保存。别忘了执行左侧动作「🚀 重建前台站点」让改动发布到网站上。",
                messages.INFO,
            )
        return response
