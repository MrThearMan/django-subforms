from __future__ import annotations

from django.apps import AppConfig

__all__ = [
    "MyAppConfig",
]


class MyAppConfig(AppConfig):
    name = "example_project.app"
    verbose_name = "app"
    default_auto_field = "django.db.models.BigAutoField"
