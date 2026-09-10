from django.contrib import admin
from django.urls import include, path

from core import views

# 函数只接管 /api/* 前缀（Vercel 的 rewrite 保证进来的 PATH_INFO 一定以 /api 开头）
urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api", views.api_root),
]

admin.site.site_header = "课题组网站管理后台"
admin.site.site_title = "课题组网站管理后台"
admin.site.index_title = "内容管理"
