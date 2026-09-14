import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings

from .models import Member, SiteSetting


class SeedContentTests(TestCase):
    def test_import_preserves_extended_content_in_public_api(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src/data').mkdir(parents=True)
            (root / 'src/content/members').mkdir(parents=True)
            (root / 'src/data/site.json').write_text(json.dumps({
                'name': '导入测试', 'groupPhoto': '/images/group.jpg',
                'pageCopy': {'home_news_title': '最新研究动态'},
            }), encoding='utf-8')
            (root / 'src/content/members/member.md').write_text(
                '---\nname: 测试成员\nrole: 博士生\nhobbies: [摄影, 跑步]\n'
                'researchFocus: 机器人感知\nachievementSummary: 开源研究工具\n---\n成员正文',
                encoding='utf-8',
            )
            with override_settings(ROOT_DIR=root, AUTO_REBUILD_ON_SAVE=False):
                for _ in range(2):
                    call_command('seed_content', stdout=StringIO())
            bundle = self.client.get('/api/content/').json()
            self.assertEqual(bundle['site']['groupPhoto'], '/images/group.jpg')
            self.assertEqual(bundle['site']['pageCopy']['home_news_title'], '最新研究动态')
            self.assertEqual(bundle['members'][0]['hobbies'], ['摄影', '跑步'])
            self.assertEqual(bundle['members'][0]['researchFocus'], '机器人感知')
            self.assertEqual(bundle['members'][0]['achievementSummary'], '开源研究工具')
            self.assertEqual(Member.objects.count(), 1)
            # Older Markdown must not erase profile fields maintained in Admin.
            (root / 'src/content/members/member.md').write_text(
                '---\nname: 更新姓名\nrole: 博士生\n---\n更新正文', encoding='utf-8',
            )
            with override_settings(ROOT_DIR=root):
                call_command('seed_content', stdout=StringIO())
            member = Member.objects.get()
            self.assertEqual(member.name, '更新姓名')
            self.assertEqual(member.hobbies, ['摄影', '跑步'])
            self.assertEqual(member.research_focus, '机器人感知')
            self.assertEqual(member.achievement_summary, '开源研究工具')

    def test_legacy_site_import_retains_new_admin_fields(self):
        site = SiteSetting.load()
        site.group_photo = '/images/existing.jpg'
        site.page_copy = {'home_news_title': '已维护文案'}
        site.save()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src/data').mkdir(parents=True)
            (root / 'src/data/site.json').write_text('{"name": "Legacy"}', encoding='utf-8')
            with override_settings(ROOT_DIR=root):
                call_command('seed_content', stdout=StringIO())
        site.refresh_from_db()
        self.assertEqual(site.group_photo, '/images/existing.jpg')
        self.assertEqual(site.page_copy, {'home_news_title': '已维护文案'})
