from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [("core", "0004_robotproject_member_profile")]
    operations = [migrations.AddField(model_name="sitesetting", name="group_photo", field=models.CharField(blank=True, help_text="可上传图片或填写公开图片地址；建议横向大图", max_length=500, verbose_name="首页团队合照"))]
