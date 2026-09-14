"""把模型转换成前端直接可用的 JSON 结构。"""

from .models import HomeSlide, Member, News, Project, Publication, ResearchArea, SiteSetting, RobotProject
from .utils import as_dict, as_list, render_markdown

DEFAULT_NAV = [
    {"label": "首页", "href": "/"},
    {"label": "研究方向", "href": "/research"},
    {"label": "团队成员", "href": "/team"},
    {"label": "科研新闻", "href": "/news"},
    {"label": "科研成果", "href": "/publications"},
    {"label": "科研项目", "href": "/projects"},
    {"label": "科研平台", "href": "/platform"},
    {"label": "加入我们", "href": "/join"},
    {"label": "联系我们", "href": "/contact"},
]


def _with_extra_nav(nav: list) -> list:
    """把后来新增的栏目补进老站点已经保存的导航里（插在「联系我们」之前）。"""
    result = list(nav)
    for label, href in (("科研平台", "/platform"), ("科研项目", "/projects"), ("加入我们", "/join")):
        if not any(isinstance(item, dict) and item.get("href") == href for item in result):
            index = next(
                (i for i, item in enumerate(result) if isinstance(item, dict) and item.get("href") == "/contact"),
                len(result),
            )
            result.insert(index, {"label": label, "href": href})
    return result


def serialize_site(obj: SiteSetting) -> dict:
    nav = _with_extra_nav(as_list(obj.nav) or DEFAULT_NAV)
    if not nav:
        nav = DEFAULT_NAV
    return {
        "name": obj.name,
        "nameEn": obj.name_en,
        "abbr": obj.abbr,
        "tagline": obj.tagline,
        "affiliation": obj.affiliation,
        "description": obj.description,
        "groupPhoto": obj.group_photo,
        "contact": {
            "address": obj.address,
            "postcode": obj.postcode,
            "email": obj.email,
            "phone": obj.phone,
        },
        "openings": {
            "enabled": obj.openings_enabled,
            "title": obj.openings_title,
            "text": obj.openings_text,
            "detailsHtml": render_markdown(obj.openings_details),
            "email": obj.openings_email,
        },
        "nav": [
            {"label": str(item.get("label", "")), "href": str(item.get("href", "/"))}
            for item in nav
            if isinstance(item, dict) and item.get("label")
        ],
        "social": [
            {"label": str(item.get("label", "")), "href": str(item.get("href", ""))}
            for item in as_list(obj.social)
            if isinstance(item, dict) and item.get("label")
        ],
        "icp": obj.icp,
        "pageCopy": obj.page_copy,
    }


def serialize_research(obj: ResearchArea) -> dict:
    return {
        "slug": obj.slug,
        "title": obj.title,
        "titleEn": obj.title_en,
        "summary": obj.summary,
        "icon": obj.icon,
        "keywords": [str(k) for k in as_list(obj.keywords)],
        "order": obj.order,
        "cover": obj.cover,
        "bodyHtml": render_markdown(obj.body),
        "updatedAt": obj.updated_at.isoformat(),
    }


def serialize_member(obj: Member) -> dict:
    return {
        "slug": obj.slug,
        "name": obj.name,
        "nameEn": obj.name_en,
        "role": obj.role,
        "title": obj.title,
        "order": obj.order,
        "photo": obj.photo,
        "email": obj.email,
        "joinYear": obj.join_year,
        "nowAt": obj.now_at,
        "areas": [str(a) for a in as_list(obj.areas)],
        "interests": [str(i) for i in as_list(obj.interests)],
        "hobbies": [str(i) for i in as_list(obj.hobbies)],
        "researchFocus": obj.research_focus,
        "achievementSummary": obj.achievement_summary,
        "links": as_dict(obj.links),
        "bioHtml": render_markdown(obj.bio),
        "updatedAt": obj.updated_at.isoformat(),
    }


def serialize_news(obj: News) -> dict:
    return {
        "slug": obj.slug,
        "title": obj.title,
        "date": obj.date.isoformat(),
        "summary": obj.summary,
        "tags": [str(t) for t in as_list(obj.tags)],
        "cover": obj.cover,
        "pinned": obj.pinned,
        "bodyHtml": render_markdown(obj.body),
        "updatedAt": obj.updated_at.isoformat(),
    }


def serialize_publication(obj: Publication) -> dict:
    return {
        "slug": obj.slug,
        "title": obj.title,
        "authors": [str(a) for a in as_list(obj.authors)],
        "venue": obj.venue,
        "venueShort": obj.venue_short,
        "year": obj.year,
        "type": obj.type,
        "area": obj.area,
        "highlight": obj.highlight,
        "link": obj.link,
        "pdf": obj.pdf,
        "code": obj.code,
        "abstract": obj.abstract,
        "bodyHtml": render_markdown(obj.abstract),
        "updatedAt": obj.updated_at.isoformat(),
    }

def serialize_robot_project(obj: RobotProject) -> dict:
    return {"slug": obj.slug, "name": obj.name, "summary": obj.summary, "researchFocus": obj.research_focus, "modelUrl": obj.model_url, "modelFormat": obj.model_format, "demoUrl": obj.demo_url, "bodyHtml": render_markdown(obj.body), "updatedAt": obj.updated_at.isoformat()}


def serialize_home_slide(obj: HomeSlide) -> dict:
    return {
        "slug": f"slide-{obj.pk}",
        "title": obj.title,
        "titleEn": obj.title_en,
        "summary": obj.summary,
        "image": obj.image,
        "link": obj.link,
        "linkLabel": obj.link_label,
        "order": obj.order,
        "updatedAt": obj.updated_at.isoformat(),
    }


def serialize_project(obj: Project) -> dict:
    return {
        "slug": obj.slug,
        "name": obj.name,
        "category": obj.category,
        "sponsor": obj.sponsor,
        "code": obj.code,
        "role": obj.role,
        "leader": obj.leader,
        "members": [str(m) for m in as_list(obj.members)],
        "startYear": obj.start_year,
        "endYear": obj.end_year,
        "status": obj.status,
        "amount": obj.amount,
        "summary": obj.summary,
        "link": obj.link,
        "order": obj.order,
        "bodyHtml": render_markdown(obj.body),
        "updatedAt": obj.updated_at.isoformat(),
    }


def serialize_content() -> dict:
    """一次性返回全站内容，构建前端时只需请求一次。"""
    return {
        "site": serialize_site(SiteSetting.load()),
        "homeSlides": [serialize_home_slide(o) for o in HomeSlide.objects.filter(published=True)],
        "research": [serialize_research(o) for o in ResearchArea.objects.filter(published=True)],
        "members": [serialize_member(o) for o in Member.objects.filter(published=True)],
        "news": [serialize_news(o) for o in News.objects.filter(published=True)],
        "publications": [serialize_publication(o) for o in Publication.objects.filter(published=True)],
        "projects": [serialize_project(o) for o in Project.objects.filter(published=True)],
        "robotProjects": [serialize_robot_project(o) for o in RobotProject.objects.filter(published=True)],
    }
