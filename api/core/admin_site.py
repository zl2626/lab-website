"""Content overview and an explicit, permission-checked publishing entry point."""

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.apps import AdminConfig
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import path, reverse

from .utils import trigger_deploy


class LabAdminConfig(AdminConfig):
    default_site = "core.admin_site.LabAdminSite"


class LabAdminSite(admin.AdminSite):
    index_template = "core/dashboard.html"
    site_url = "/"

    def each_context(self, request):
        context = super().each_context(request)
        context["site_url"] = settings.SITE_BASE_URL or ("http://127.0.0.1:4321/" if settings.DEBUG else "/")
        context["local_preview"] = settings.DEBUG and not settings.VERCEL_DEPLOY_HOOK_URL
        return context

    def get_urls(self):
        return [path("publish/", self.admin_view(self.publish), name="publish")] + super().get_urls()

    def publish(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        ok, message = trigger_deploy()
        messages.add_message(request, messages.SUCCESS if ok else messages.WARNING, message)
        return redirect("admin:index")

    def index(self, request, extra_context=None):
        from .models import HomeSlide, Member, News, Project, Publication, ResearchArea, RobotProject, SiteSetting

        cards = []
        site_setting = self._registry.get(SiteSetting)
        if site_setting and site_setting.has_view_or_change_permission(request):
            setting = SiteSetting.load()
            cards.append({
                "label": "站点设置与页面文案",
                "total": 1,
                "published": 1,
                "drafts": 0,
                "url": reverse("admin:core_sitesetting_change", args=[setting.pk]),
                "draft_url": reverse("admin:core_sitesetting_change", args=[setting.pk]),
                "add_url": None,
            })
        recent = []
        name_models = (Member, RobotProject, Project)
        for model in (HomeSlide, ResearchArea, Member, News, Publication, Project, RobotProject):
            model_admin = self._registry[model]
            if not model_admin.has_view_or_change_permission(request):
                continue
            counts = model.objects.aggregate(total=Count("pk"), published=Count("pk", filter=Q(published=True)))
            name = model._meta.model_name
            list_url = reverse(f"admin:core_{name}_changelist")
            display_field = "name" if model in name_models else "title"
            for obj in model.objects.only("pk", "updated_at", "published", display_field).order_by("-updated_at", "-pk")[:8]:
                recent.append({
                    "title": getattr(obj, display_field),
                    "label": model._meta.verbose_name,
                    "updated_at": obj.updated_at,
                    "published": obj.published,
                    "url": reverse(f"admin:core_{name}_change", args=[obj.pk]),
                })
            cards.append({
                "label": model._meta.verbose_name_plural,
                "total": counts["total"],
                "published": counts["published"],
                "drafts": counts["total"] - counts["published"],
                "url": list_url,
                "draft_url": f"{list_url}?published__exact=0",
                "add_url": reverse(f"admin:core_{name}_add") if model_admin.has_add_permission(request) else None,
            })
        return super().index(request, {
            **(extra_context or {}),
            "content_cards": cards,
            "recent_content": sorted(recent, key=lambda item: item["updated_at"], reverse=True)[:8],
            "deploy_configured": bool(settings.VERCEL_DEPLOY_HOOK_URL),
            "auto_rebuild": settings.AUTO_REBUILD_ON_SAVE,
        })
