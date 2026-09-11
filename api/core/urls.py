from django.urls import path

from . import views

# 挂载在 labbackend/urls.py 的 "api/" 前缀下，因此这里都是 /api/xxx
urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("health/", views.health, name="health"),
    path("media/<path:path>", views.media, name="media"),
    path("content/", views.content, name="content"),
    path("site/", views.site, name="site"),
    path("research/", views.research_list, name="research-list"),
    path("research/<slug:slug>/", views.research_detail, name="research-detail"),
    path("members/", views.member_list, name="member-list"),
    path("members/<slug:slug>/", views.member_detail, name="member-detail"),
    path("news/", views.news_list, name="news-list"),
    path("news/<slug:slug>/", views.news_detail, name="news-detail"),
    path("publications/", views.publication_list, name="publication-list"),
    path("publications/<slug:slug>/", views.publication_detail, name="publication-detail"),
]
