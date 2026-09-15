"""Isolated tests: never connect to the database or deploy hook in .env.local."""
from .settings import *  # noqa: F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
VERCEL_DEPLOY_HOOK_URL = ""
VERCEL_API_TOKEN = ""
VERCEL_PROJECT_ID = ""
VERCEL_TEAM_ID = ""
DEEPSEEK_API_KEY = ""
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SECURE_SSL_REDIRECT = False
