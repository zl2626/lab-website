from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0003_sitesetting_page_copy")]
    operations = [
        migrations.AddField(model_name="member", name="hobbies", field=models.JSONField(default=list, blank=True, verbose_name="兴趣爱好")),
        migrations.AddField(model_name="member", name="research_focus", field=models.CharField(default="", max_length=200, blank=True, verbose_name="主要研究方向")),
        migrations.AddField(model_name="member", name="achievement_summary", field=models.TextField(default="", blank=True, help_text="用通俗语言写论文、项目或比赛成果", verbose_name="成果产出")),
        migrations.CreateModel(name="RobotProject", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("published", models.BooleanField(default=True, help_text="取消勾选后前台不显示", verbose_name="发布")),
            ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")), ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ("slug", models.SlugField(max_length=120, unique=True, verbose_name="项目短名")), ("name", models.CharField(max_length=200, verbose_name="项目名称")), ("summary", models.TextField(blank=True, verbose_name="项目介绍")), ("research_focus", models.CharField(blank=True, max_length=200, verbose_name="研究方向")), ("model_url", models.URLField(blank=True, max_length=500, verbose_name="3D 模型地址")), ("model_format", models.CharField(blank=True, help_text="例如 GLB、OBJ、STL", max_length=30, verbose_name="模型格式")), ("demo_url", models.URLField(blank=True, max_length=500, verbose_name="演示视频地址")), ("body", models.TextField(blank=True, verbose_name="详细说明")), ("order", models.IntegerField(default=99, verbose_name="排序"))], options={"ordering":["order","-updated_at","id"],"verbose_name":"机器人项目","verbose_name_plural":"科研平台·机器人项目"}),
    ]
