from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_mediafile")]
    operations = [migrations.AddField(
        model_name="sitesetting", name="page_copy",
        field=models.JSONField("各页面文案", default=dict, blank=True),
    )]
