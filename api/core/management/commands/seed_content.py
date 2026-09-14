"""把仓库里的 Markdown 内容导入数据库。

用法：
    python api/manage.py seed_content            # 增量导入 / 更新（按 slug 覆盖）
    python api/manage.py seed_content --clear    # 先清空再导入

覆盖内容：
    src/data/site.json          -> SiteSetting
    src/content/research/*.md   -> ResearchArea
    src/content/members/*.md    -> Member
    src/content/news/*.md       -> News
    src/content/publications/*.md -> Publication
"""

import json
from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Member, News, Publication, ResearchArea, SiteSetting
from core.utils import as_list


def parse_markdown(path: Path) -> tuple[dict, str]:
    """拆分 Markdown 的 YAML frontmatter 与正文。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()

    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, text.strip()

    front = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :]).strip()
    return (yaml.safe_load(front) or {}), body


class Command(BaseCommand):
    help = "从 src/content 与 src/data/site.json 导入初始内容到数据库"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="导入前先清空现有内容")

    @transaction.atomic
    def handle(self, *args, **options):
        root: Path = settings.ROOT_DIR
        content_dir = root / "src" / "content"

        if options["clear"]:
            for model in (ResearchArea, Member, News, Publication):
                model.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空原有内容。"))

        counts = {
            "site": self._seed_site(root),
            "research": self._seed(
                content_dir / "research", ResearchArea, self._research_fields
            ),
            "members": self._seed(content_dir / "members", Member, self._member_fields),
            "news": self._seed(content_dir / "news", News, self._news_fields),
            "publications": self._seed(
                content_dir / "publications", Publication, self._publication_fields
            ),
        }

        for name, count in counts.items():
            self.stdout.write(self.style.SUCCESS(f"  {name}: {count} 条"))

        self.stdout.write(self.style.SUCCESS("内容导入完成。"))

    # ------------------------------------------------------------------
    def _seed_site(self, root: Path) -> int:
        path = root / "src" / "data" / "site.json"
        if not path.exists():
            return 0
        data = json.loads(path.read_text(encoding="utf-8"))
        site = SiteSetting.load()
        contact = data.get("contact", {}) or {}
        openings = data.get("openings", {}) or {}

        site.name = data.get("name", site.name)
        site.name_en = data.get("nameEn", "")
        site.abbr = data.get("abbr", site.abbr)
        site.tagline = data.get("tagline", "")
        site.affiliation = data.get("affiliation", "")
        site.description = data.get("description", "")
        site.group_photo = data.get("groupPhoto", site.group_photo)
        site.page_copy = {**site.page_copy, **data.get("pageCopy", {})}
        site.address = contact.get("address", "")
        site.postcode = contact.get("postcode", "")
        site.email = contact.get("email", "")
        site.phone = contact.get("phone", "")
        site.openings_enabled = bool(openings.get("enabled", True))
        site.openings_title = openings.get("title", "")
        site.openings_text = openings.get("text", "")
        # 招生详情属于后台长期维护的内容，site.json 未提供时保留现有值
        if "details" in openings:
            site.openings_details = openings["details"] or ""
        site.openings_email = openings.get("email", "")
        site.nav = data.get("nav", [])
        site.social = data.get("social", [])
        site.icp = data.get("icp", "")
        site.save()
        return 1

    def _seed(self, folder: Path, model, mapper) -> int:
        if not folder.exists():
            return 0
        count = 0
        for path in sorted(folder.glob("*.md")):
            front, body = parse_markdown(path)
            slug = str(front.get("slug") or path.stem).strip()
            fields = mapper(front, body, path.stem, slug)

            # 跳过 draft 的内容
            if front.get("draft") is True and "published" not in fields:
                continue

            model.objects.update_or_create(slug=slug, defaults=fields)
            count += 1
        return count

    # ------------------------------------------------------------------
    def _research_fields(self, front: dict, body: str, stem: str, slug: str) -> dict:
        return {
            "title": front.get("title", stem),
            "title_en": front.get("titleEn", ""),
            "summary": front.get("summary", ""),
            "icon": front.get("icon", "🔬"),
            "keywords": as_list(front.get("keywords")),
            "order": int(front.get("order", 99)),
            "cover": front.get("cover", "") or "",
            "body": body,
            "published": not bool(front.get("draft", False)),
        }

    def _member_fields(self, front: dict, body: str, stem: str, slug: str) -> dict:
        return {
            "name": front.get("name", stem),
            "name_en": front.get("nameEn", ""),
            "role": front.get("role", Member.Role.PHD),
            "title": front.get("title", ""),
            "order": int(front.get("order", 99)),
            "photo": front.get("photo", "") or "",
            "email": front.get("email", "") or "",
            "join_year": str(front.get("joinYear", "") or ""),
            "interests": as_list(front.get("interests")),
            **({"now_at": front["nowAt"] or ""} if "nowAt" in front else {}),
            **({"areas": as_list(front["areas"])} if "areas" in front else {}),
            **({"hobbies": as_list(front["hobbies"])} if "hobbies" in front else {}),
            **({"research_focus": front["researchFocus"] or ""} if "researchFocus" in front else {}),
            **({"achievement_summary": front["achievementSummary"] or ""} if "achievementSummary" in front else {}),
            "links": front.get("links") or {},
            "bio": body,
            "published": not bool(front.get("draft", False)),
        }

    def _news_fields(self, front: dict, body: str, stem: str, slug: str) -> dict:
        return {
            "title": front.get("title", stem),
            "date": front.get("date"),
            "summary": front.get("summary", "") or "",
            "tags": as_list(front.get("tags")),
            "cover": front.get("cover", "") or "",
            "pinned": bool(front.get("pinned", False)),
            "body": body,
            "published": not bool(front.get("draft", False)),
        }

    def _publication_fields(self, front: dict, body: str, stem: str, slug: str) -> dict:
        return {
            "title": front.get("title", stem),
            "authors": as_list(front.get("authors")),
            "venue": front.get("venue", ""),
            "venue_short": front.get("venueShort", ""),
            "year": int(front.get("year", 0)),
            "type": front.get("type", Publication.Type.CONFERENCE),
            "area": front.get("area", "") or "",
            "highlight": bool(front.get("highlight", False)),
            "link": front.get("link", "") or "",
            "pdf": front.get("pdf", "") or "",
            "code": front.get("code", "") or "",
            "abstract": body,
            "published": not bool(front.get("draft", False)),
        }
