"""Verify admin saves against the running local frontend, then restore settings."""
import os
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
os.environ["DJANGO_SETTINGS_MODULE"] = "labbackend.settings"
os.environ["DATABASE_URL"] = ""
os.environ["DJANGO_DEBUG"] = "1"

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.test import Client, override_settings
from core.admin import SiteSettingForm
from core.models import SiteSetting

assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
assert Path(settings.DATABASES["default"]["NAME"]).resolve() == ROOT / "db.sqlite3"


def main():
    # Check both servers before touching local content.
    for url in ("http://127.0.0.1:8000/api/health/", "http://127.0.0.1:4321/"):
        with urlopen(url, timeout=30) as response:
            assert response.status == 200
    owner = get_user_model().objects.filter(is_superuser=True, is_active=True).first()
    if owner is None:
        raise RuntimeError("A local administrator is required.")
    site = SiteSetting.objects.get(pk=1)
    original = model_to_dict(site)
    original.pop("id", None)
    original["updated_at"] = site.updated_at
    form = SiteSettingForm(instance=site)
    data = {}
    for name, field in form.fields.items():
        value = form[name].value()
        if isinstance(value, bool):
            if value:
                data[name] = "on"
        else:
            data[name] = "" if value is None else value
    checks = {
        "/": "home_news_title", "/research": "research_title",
        "/team": "team_title", "/news": "news_title",
        "/publications": "publications_title", "/contact": "contact_title",
    }
    for key in checks.values():
        data[f"copy_{key}"] = f"CMS-ROUNDTRIP-{key}"
    data["copy_footer_copyright"] = "CMS-ROUNDTRIP-footer"
    client = Client()
    client.force_login(owner)
    try:
        with override_settings(AUTO_REBUILD_ON_SAVE=False):
            response = client.post("/api/admin/core/sitesetting/1/change/", data)
        assert response.status_code == 302, "Admin save failed"
        site.refresh_from_db()
        for route, key in checks.items():
            marker = data[f"copy_{key}"]
            assert site.page_copy[key] == marker
            with urlopen(f"http://127.0.0.1:4321{route}", timeout=30) as response:
                html = response.read().decode("utf-8")
            assert marker in html, f"Saved content missing from {route}"
            assert "CMS-ROUNDTRIP-footer" in html, f"Footer missing from {route}"
            print(f"PASS admin -> database -> frontend: {route}")
    finally:
        SiteSetting.objects.filter(pk=site.pk).update(**original)
        client.logout()
        print("Original local settings restored.")
    with urlopen("http://127.0.0.1:4321/", timeout=30) as response:
        assert "CMS-ROUNDTRIP-" not in response.read().decode("utf-8")
    print("PASS restored content visible without restarting frontend")


if __name__ == "__main__":
    main()
