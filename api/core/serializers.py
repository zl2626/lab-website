"""把模型转换成前端直接可用的 JSON 结构。"""

from .models import HomeSlide, Member, News, Project, Publication, ResearchArea, SiteSetting, RobotProject
from .utils import as_dict, as_list, render_markdown

DEFAULT_NAV = [
    {"label": "首页", "href": "/"},
    {"label": "团队成员", "href": "/team"},
    {"label": "科研平台", "href": "/platform"},
    {"label": "科研成果", "href": "/publications"},
    {"label": "加入我们", "href": "/join"},
]


# ---------------------------------------------------------------------------
# 历史版本发布过的默认菜单（只记 href 顺序）
# ---------------------------------------------------------------------------
# 老站点在升级前把当时的默认菜单存进了数据库，后来新增的栏目不会自己出现。
# 这里做一次性「补栏目」，但**只在导航仍然是某个历史默认菜单时**才动手：
# 管理员一旦增删过导航，就以他自己的配置为准，自动化不再插手。
# 教训：曾经的做法是「缺哪个就补哪个」，结果管理员删掉「科研平台」保存后
# 前台又被自动插回来 —— 后台的删除动作等于失效。
LEGACY_DEFAULT_NAV_HREFS = [
    # 第三版：9 项（本次精简前的默认菜单）
    ["/", "/research", "/team", "/news", "/publications", "/projects", "/platform", "/join", "/contact"],
    # 第一版：6 项（没有科研平台 / 科研项目 / 加入我们）
    ["/", "/research", "/team", "/news", "/publications", "/contact"],
    # 第二版：7 项（补了科研平台）
    ["/", "/research", "/team", "/news", "/publications", "/platform", "/contact"],
]


def _nav_hrefs(nav: list) -> list:
    return [str(item.get("href", "")) for item in nav if isinstance(item, dict)]


def _rescue_legacy_nav(nav: list) -> list:
    """导航仍是历史默认菜单时补上新增栏目；管理员动过就原样返回。"""
    if _nav_hrefs(nav) in LEGACY_DEFAULT_NAV_HREFS:
        return [dict(item) for item in DEFAULT_NAV]
    return nav


def serialize_site(obj: SiteSetting) -> dict:
    nav = [item for item in as_list(obj.nav) if isinstance(item, dict) and item.get("label")]
    # 留空 = 用默认菜单；历史默认菜单自动补新栏目；其余按管理员自己的配置原样输出
    nav = _rescue_legacy_nav(nav) if nav else [dict(item) for item in DEFAULT_NAV]
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
