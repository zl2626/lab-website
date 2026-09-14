"""公开 JSON 接口（只读）。

前端在构建时调用 /api/content/ 拉取全站内容；
如果接口不可用，前端会自动回退到仓库里的 Markdown 文件。
"""

from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from .models import HomeSlide, MediaFile, Member, News, Publication, ResearchArea, SiteSetting
from .serializers import (
    serialize_content,
    serialize_home_slide,
    serialize_member,
    serialize_news,
    serialize_publication,
    serialize_research,
    serialize_site,
)


def _json(data, status: int = 200) -> JsonResponse:
    # ensure_ascii=False 保证中文不被转义成 \uXXXX；safe 允许直接返回数组
    return JsonResponse(
        data,
        status=status,
        safe=not isinstance(data, list),
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def api_root(request):
    return _json(
        {
            "name": "课题组网站内容接口",
            "endpoints": [
                "/api/health/",
                "/api/content/",
                "/api/site/",
                "/api/home-slides/",
                "/api/research/",
                "/api/research/<slug>/",
                "/api/members/",
                "/api/members/<slug>/",
                "/api/news/",
                "/api/news/<slug>/",
                "/api/publications/",
                "/api/publications/<slug>/",
            ],
        }
    )


@require_GET
def health(request):
    return _json({"status": "ok"})


@require_GET
def media(request, path: str):
    """提供后台里上传的图片。

    文件名是内容哈希，内容变了名字才会变，因此可以放心用一年强缓存。
    """
    record = MediaFile.objects.filter(name=path).first()
    if record is None:
        raise Http404("图片不存在")

    response = HttpResponse(bytes(record.data), content_type=record.content_type)
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["Content-Length"] = str(record.size)
    return response


@require_GET
def content(request):
    """构建前端时使用：一次请求拿全站内容。"""
    return _json(serialize_content())


@require_GET
def home_slide_list(request):
    return _json([serialize_home_slide(o) for o in HomeSlide.objects.filter(published=True)])


@require_GET
def site(request):
    return _json(serialize_site(SiteSetting.load()))


@require_GET
def research_list(request):
    return _json(
        [serialize_research(o) for o in ResearchArea.objects.filter(published=True)]
    )


@require_GET
def research_detail(request, slug: str):
    try:
        obj = ResearchArea.objects.get(slug=slug, published=True)
    except ResearchArea.DoesNotExist as exc:
        raise Http404("研究方向不存在") from exc
    return _json(serialize_research(obj))


@require_GET
def member_list(request):
    return _json([serialize_member(o) for o in Member.objects.filter(published=True)])


@require_GET
def member_detail(request, slug: str):
    try:
        obj = Member.objects.get(slug=slug, published=True)
    except Member.DoesNotExist as exc:
        raise Http404("成员不存在") from exc
    return _json(serialize_member(obj))


@require_GET
def news_list(request):
    return _json([serialize_news(o) for o in News.objects.filter(published=True)])


@require_GET
def news_detail(request, slug: str):
    try:
        obj = News.objects.get(slug=slug, published=True)
    except News.DoesNotExist as exc:
        raise Http404("新闻不存在") from exc
    return _json(serialize_news(obj))


@require_GET
def publication_list(request):
    return _json(
        [serialize_publication(o) for o in Publication.objects.filter(published=True)]
    )


@require_GET
def publication_detail(request, slug: str):
    try:
        obj = Publication.objects.get(slug=slug, published=True)
    except Publication.DoesNotExist as exc:
        raise Http404("成果不存在") from exc
    return _json(serialize_publication(obj))
