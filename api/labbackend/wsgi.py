"""WSGI 入口（本地 `python api/manage.py runserver` 与 Vercel 都指向它）。"""

import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labbackend.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
