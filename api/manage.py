#!/usr/bin/env python
"""Django 命令行入口。

用法（在仓库根目录执行）：
    python api/manage.py migrate
    python api/manage.py createsuperuser
    python api/manage.py seed_content
"""

import os
import sys
from pathlib import Path


def main() -> None:
    api_dir = Path(__file__).resolve().parent
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labbackend.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "无法导入 Django。请先安装依赖：pip install -r requirements.txt"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
