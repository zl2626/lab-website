from datetime import date
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import News


class AdminWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser("owner", "", "test-password")
        cls.viewer = get_user_model().objects.create_user("viewer", is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_news"))
        cls.news = News.objects.create(slug="draft", title="未发布新闻", date=date.today(), published=False)

    def test_dashboard_respects_model_permissions(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "网站工作台")
        self.assertEqual(len(response.context["content_cards"]), 1)
        self.assertEqual(response.context["content_cards"][0]["drafts"], 1)
        self.assertNotContains(response, "重建并发布官网")
        self.assertNotContains(response, "新增科研新闻")
        self.assertEqual(len(response.context["recent_content"]), 1)
        self.assertEqual(response.context["recent_content"][0]["title"], "未发布新闻")
        self.assertContains(response, "published__exact=0")

    @patch("core.admin_site.trigger_deploy", return_value=(True, "已请求重建"))
    def test_publish_requires_superuser_and_post(self, deploy):
        url = reverse("admin:publish")
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 405)
        deploy.assert_not_called()
        self.assertRedirects(self.client.post(url), reverse("admin:index"))
        deploy.assert_called_once()

    @patch("core.admin_site.trigger_deploy")
    def test_publish_requires_csrf(self, deploy):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(reverse("admin:publish")).status_code, 403)
        deploy.assert_not_called()

    def test_viewer_cannot_generate_summary(self):
        from django.test import RequestFactory
        request = RequestFactory().get("/")
        request.user = self.viewer
        actions = admin.site._registry[News].get_actions(request)
        self.assertNotIn("ai_make_summary", actions)
        self.assertNotIn("rebuild_site", actions)

    @override_settings(AUTO_REBUILD_ON_SAVE=True)
    @patch("core.admin.trigger_deploy", return_value=(True, "已请求重建"))
    @patch("core.admin.generate_summary", return_value="新摘要")
    def test_ai_summary_schedules_one_rebuild(self, generate, deploy):
        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("admin:core_news_changelist"), {
                "action": "ai_make_summary", "_selected_action": [self.news.pk],
            })
        self.assertEqual(response.status_code, 302)
        self.news.refresh_from_db()
        self.assertEqual(self.news.summary, "新摘要")
        deploy.assert_called_once()

    def test_public_api_excludes_drafts(self):
        self.assertEqual(self.client.get("/api/news/").json(), [])
        self.assertEqual(self.client.get("/api/news/draft/").status_code, 404)

    def test_recent_updates_can_all_come_from_one_model(self):
        for index in range(9):
            News.objects.create(slug=f"recent-{index}", title=f"更新 {index}", date=date.today())
        self.client.force_login(self.viewer)
        recent = self.client.get(reverse("admin:index")).context["recent_content"]
        self.assertEqual(len(recent), 8)
        self.assertEqual(recent[0]["title"], "更新 8")


class EditorFieldTests(TestCase):
    def test_links_reject_whitespace_and_protocol_relative_urls(self):
        from django import forms
        from .forms import LinkListField
        for url in ("//example.com", "/\t/example.com", "/bad path", "javascript:alert(1)"):
            with self.subTest(url=url), self.assertRaises(forms.ValidationError):
                LinkListField().clean(f"链接 | {url}")

    def test_image_forms_submit_multipart_files(self):
        from .admin import MemberForm, NewsForm, ResearchAreaForm
        for form in (MemberForm, NewsForm, ResearchAreaForm):
            self.assertTrue(form().is_multipart(), form.__name__)

    def test_line_input_preserves_author_order_and_commas(self):
        from .forms import LineListField
        field = LineListField()
        self.assertEqual(field.clean("  Wang, Qiang\r\n\r\n张伟  "), ["Wang, Qiang", "张伟"])
        self.assertEqual(field.prepare_value(["Wang, Qiang", "张伟"]), "Wang, Qiang\n张伟")
        self.assertEqual(field.clean(""), [])

    def test_existing_json_arrays_are_supported_but_invalid_entries_rejected(self):
        from django import forms
        from .forms import LineListField
        field = LineListField()
        self.assertEqual(field.clean('["视觉", "学习"]'), ["视觉", "学习"])
        for value in ('[broken', '[{"name":"张伟"}]', '[1]', {"name": "张伟"}):
            with self.assertRaises(forms.ValidationError):
                field.clean(value)

    def test_news_form_saves_list_and_reload_displays_lines(self):
        from .admin import NewsForm
        form = NewsForm(data={"slug": "editor-test", "title": "表单测试", "date": "2026-09-13", "tags": "研究进展\n获奖", "published": True})
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save()
        obj.refresh_from_db()
        self.assertEqual(obj.tags, ["研究进展", "获奖"])
        self.assertEqual(NewsForm(instance=obj)["tags"].value(), "研究进展\n获奖")


@override_settings(AUTO_REBUILD_ON_SAVE=False)
class ContentPersistenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("editor", "", "test-password")
        self.client.force_login(self.user)

    def test_every_content_admin_saves_updates_and_unpublishes(self):
        from .models import Member, Publication, ResearchArea
        cases = [
            (ResearchArea, "research", {"slug": "roundtrip-research", "title": "研究保存", "summary": "研究摘要", "icon": "🔬", "order": 1, "keywords": "感知\n学习", "body": "**方向正文**"}),
            (Member, "members", {"slug": "roundtrip-member", "name": "成员保存", "role": "博士生", "order": 1, "interests": "视觉\n机器人", "links": "github | https://github.com/example", "bio": "**成员正文**"}),
            (News, "news", {"slug": "roundtrip-news", "title": "新闻保存", "date": "2026-09-13", "tags": "新闻\n活动", "body": "**新闻正文**", "summary": "新闻摘要"}),
            (Publication, "publications", {"slug": "roundtrip-publication", "title": "成果保存", "year": 2026, "venue": "Test Venue", "authors": "Wang, Qiang\n张伟", "type": "会议论文", "abstract": "成果正文"}),
        ]
        for model, endpoint, data in cases:
            with self.subTest(model=model.__name__):
                data = {**data, "published": "on"}
                base = f"admin:core_{model._meta.model_name}"
                response = self.client.post(reverse(base + "_add"), data)
                self.assertEqual(response.status_code, 302, getattr(response, "context", None))
                obj = model.objects.get(slug=data["slug"])
                public = self.client.get(f"/api/{endpoint}/").json()
                self.assertEqual(public[0]["slug"], obj.slug)
                name = "name" if model is Member else "title"
                data[name] += "已更新"
                self.assertEqual(self.client.post(reverse(base + "_change", args=[obj.pk]), data).status_code, 302)
                obj.refresh_from_db()
                self.assertEqual(getattr(obj, name), data[name])
                self.assertEqual(self.client.get(f"/api/{endpoint}/").json()[0][name], data[name])
                data.pop("published")
                self.assertEqual(self.client.post(reverse(base + "_change", args=[obj.pk]), data).status_code, 302)
                self.assertEqual(self.client.get(f"/api/{endpoint}/").json(), [])
                self.assertEqual(self.client.post(reverse(base + "_delete", args=[obj.pk]), {"post": "yes"}).status_code, 302)
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_site_settings_all_page_copy_survives_save_and_reload(self):
        from .forms import PAGE_COPY
        from .models import SiteSetting
        obj = SiteSetting.load()
        data = {"name": "保存后的实验室", "abbr": "TEST", "email": "lab@example.com", "nav": "首页 | /\n研究 | /research", "social": "主页 | https://example.com", "openings_title": "招生保存", "openings_text": "说明保存", "openings_enabled": "on"}
        for key, spec in PAGE_COPY.items():
            data[f"copy_{key}"] = "https://example.com/map" if spec["type"] == "url" else f"测试文案-{key}"
        url = reverse("admin:core_sitesetting_change", args=[obj.pk])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.name, data["name"])
        self.assertEqual(len(obj.page_copy), len(PAGE_COPY))
        bundle = self.client.get("/api/content/").json()["site"]
        self.assertEqual(bundle["pageCopy"], obj.page_copy)
        nav_hrefs = [item["href"] for item in bundle["nav"]]
        self.assertIn("/research", nav_hrefs)
        self.assertIn("/platform", nav_hrefs)
        self.assertContains(self.client.get(url), "测试文案-contact_intro")
        # Invalid navigation must produce a form error, without overwriting saved data.
        data["nav"] = "危险链接 | javascript:alert(1)"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("nav", response.context["adminform"].form.errors)
        obj.refresh_from_db()
        saved_hrefs = [item["href"] for item in obj.nav]
        self.assertIn("/research", saved_hrefs)

    def test_member_photo_upload_persists_and_is_served(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Member, MediaFile
        buffer = io.BytesIO()
        Image.new("RGB", (12, 12), "blue").save(buffer, format="PNG")
        response = self.client.post(reverse("admin:core_member_add"), {
            "slug": "photo-test", "name": "上传测试", "role": "博士生", "order": 1, "published": "on",
            "photo__upload": SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png"),
        })
        self.assertEqual(response.status_code, 302)
        obj = Member.objects.get(slug="photo-test")
        self.assertTrue(obj.photo.startswith("/api/media/"))
        self.assertEqual(MediaFile.objects.count(), 1)
        media = self.client.get(obj.photo)
        self.assertEqual(media.status_code, 200)
        self.assertEqual(media["Content-Type"], "image/jpeg")
        self.assertGreater(len(media.content), 0)

    def test_member_areas_and_alumni_destination_round_trip(self):
        """成员的去向与所属研究方向需要能通过后台逐行填写，并出现在公开接口里。"""
        from .models import Member
        response = self.client.post(reverse("admin:core_member_add"), {
            "slug": "alumni-test", "name": "测试校友", "role": "校友", "order": 5,
            "published": "on", "now_at": "某公司 算法研究员",
            "areas": "计算机视觉\n多模态学习",
        })
        self.assertEqual(response.status_code, 302)

        obj = Member.objects.get(slug="alumni-test")
        self.assertEqual(obj.now_at, "某公司 算法研究员")
        self.assertEqual(obj.areas, ["计算机视觉", "多模态学习"])

        member = next(item for item in self.client.get("/api/members/").json() if item["slug"] == "alumni-test")
        self.assertEqual(member["nowAt"], "某公司 算法研究员")
        self.assertEqual(member["areas"], ["计算机视觉", "多模态学习"])

    def test_openings_details_renders_markdown_in_content_api(self):
        """招生详情存 Markdown，接口输出渲染后的 HTML，供联系页直接注入。"""
        from .models import SiteSetting
        obj = SiteSetting.load()
        response = self.client.post(reverse("admin:core_sitesetting_change", args=[obj.pk]), {
            "name": obj.name, "abbr": obj.abbr, "openings_enabled": "on",
            "openings_details": "## 申请材料\n\n- 个人简历\n- 成绩单",
        })
        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertIn("## 申请材料", obj.openings_details)

        html = self.client.get("/api/content/").json()["site"]["openings"]["detailsHtml"]
        self.assertIn("<h2", html)
        self.assertIn("个人简历", html)
        self.assertIn("<li>", html)


class AdminCoverageTests(TestCase):
    """后台必须能改到每一处内容。

    历史坑：给模型加了字段却忘记加进 ModelAdmin.fieldsets，
    字段在后台根本不会出现，POST 也存不进去，而且不会报错。
    这里用测试把它锁死：任何「模型里有、后台里没有」的字段都会让测试失败。
    """

    # 有意不在后台直接编辑的字段：page_copy 由逐条文案字段（copy_xxx）代理
    INTENTIONALLY_HIDDEN = {"SiteSetting": {"page_copy"}}

    def setUp(self):
        self.user = get_user_model().objects.create_superuser("coverage", "", "test-password")
        self.client.force_login(self.user)

    def _request(self):
        from django.test import RequestFactory
        request = RequestFactory().get("/admin/")
        request.user = self.user
        return request

    def test_every_model_field_is_reachable_from_admin(self):
        from django.contrib import admin as dj_admin
        from .models import (
            HomeSlide, Member, News, Project, Publication, ResearchArea, RobotProject, SiteSetting,
        )

        request = self._request()
        models = (HomeSlide, ResearchArea, Member, News, Publication, Project, RobotProject, SiteSetting)
        for model in models:
            with self.subTest(model=model.__name__):
                admin_class = dj_admin.site._registry[model]
                listed = set()
                for _title, options in admin_class.get_fieldsets(request, None):
                    listed.update(options.get("fields", ()))
                listed.update(getattr(admin_class, "readonly_fields", ()))

                # 自动生成的主键不需要（也不应该）在后台出现
                editable = {
                    f.name for f in model._meta.fields if f.editable and not f.auto_created
                }
                hidden = self.INTENTIONALLY_HIDDEN.get(model.__name__, set())
                missing = editable - listed - hidden
                self.assertEqual(
                    missing, set(),
                    f"{model.__name__} 的这些字段没有出现在后台分组里，管理者改不到：{sorted(missing)}",
                )

    def test_every_page_copy_key_has_an_admin_field(self):
        """page_copy.json 里每一条文案都要能在后台编辑，否则文案是「配了但改不了」。"""
        from .admin import SiteSettingForm
        from .forms import PAGE_COPY

        form = SiteSettingForm()
        missing = [key for key in PAGE_COPY if f"copy_{key}" not in form.fields]
        self.assertEqual(missing, [], f"这些文案键没有对应的后台字段：{missing}")

    def test_page_copy_defaults_are_all_non_empty_or_intentionally_blank(self):
        """默认值不能是空白：空默认会让前台出现「改了也不知道原来写什么」的空洞。"""
        from .forms import PAGE_COPY

        blanks = [key for key, spec in PAGE_COPY.items() if not str(spec["default"]).strip()]
        self.assertEqual(
            blanks, ["contact_map_text", "contact_map_url"],
            f"出现未预期的空白默认值：{blanks}",
        )

    def test_home_slides_are_manageable_and_exposed_to_the_frontend(self):
        """首页轮播要在后台增删改，并通过接口提供给前端。"""
        from django.contrib import admin as dj_admin
        from .models import HomeSlide

        self.assertIn(HomeSlide, dj_admin.site._registry)
        admin_class = dj_admin.site._registry[HomeSlide]
        self.assertTrue(admin_class.has_add_permission(self._request()))

        HomeSlide.objects.create(title="第一屏", summary="说明", link="/team", link_label="看看团队", order=1)
        HomeSlide.objects.create(title="未发布屏", order=2, published=False)

        slides = self.client.get("/api/content/").json()["homeSlides"]
        self.assertEqual([slide["title"] for slide in slides], ["第一屏"])
        self.assertEqual(slides[0]["link"], "/team")
        self.assertEqual(slides[0]["linkLabel"], "看看团队")

    def test_projects_are_manageable_and_link_members(self):
        """科研项目要在后台维护，并能把参与成员链接到成员页。"""
        from django.contrib import admin as dj_admin
        from .models import Member, Project

        self.assertIn(Project, dj_admin.site._registry)
        response = self.client.post(reverse("admin:core_project_add"), {
            "slug": "project-test", "name": "测试项目", "category": "基金项目",
            "sponsor": "测试资助机构", "code": "TEST-001", "role": "主持",
            "leader": "张伟", "members": "张伟\n李娜", "start_year": "2025",
            "status": "在研", "order": "1", "published": "on",
        })
        # 302 可能是「保存成功」，也可能是「没登录被踢回登录页」，必须区分开
        if response.status_code != 302:
            self.fail(f"后台保存失败：{dict(response.context['adminform'].form.errors)}")
        self.assertTrue(Project.objects.filter(slug="project-test").exists())

        project = Project.objects.get(slug="project-test")
        self.assertEqual(project.members, ["张伟", "李娜"])
        self.assertEqual(project.start_year, 2025)

        # 参与成员与成员页的姓名一致时，前端才能生成链接 —— 这里校验接口给出的原始数据
        payload = self.client.get("/api/content/").json()["projects"][0]
        self.assertEqual(payload["name"], "测试项目")
        self.assertEqual(payload["members"], ["张伟", "李娜"])
        self.assertEqual(payload["startYear"], 2025)
        self.assertEqual(payload["status"], "在研")

        Member.objects.create(slug="member-x", name="张伟", name_en="Wei Zhang", role=Member.Role.PI)
        self.assertTrue(
            any(m.name_en == "Wei Zhang" for m in Member.objects.all()),
            "成员的英文名与成果署名共用同一套匹配规则",
        )

    def test_member_role_accepts_custom_values(self):
        """成员身份不再写死：实验室自己的叫法（访问学者等）也要能填、能按顺序分组。"""
        from .models import Member

        member = Member.objects.create(slug="visiting", name="访问学者甲", role="访问学者")
        payload = next(
            item for item in self.client.get("/api/members/").json() if item["slug"] == "visiting"
        )
        self.assertEqual(payload["role"], "访问学者")
        self.assertEqual(member.role, "访问学者")
