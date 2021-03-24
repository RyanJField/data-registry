#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    registry_type = os.environ.get("SCRC_REGISTRY")
    if registry_type == "local":
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drams.local-settings')
        os.environ.setdefault('DJANGO_SUPERUSER_USERNAME', 'admin')
        os.environ.setdefault('DJANGO_SUPERUSER_PASSWORD', 'admin')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drams.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
