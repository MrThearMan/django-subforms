from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create test data."

    def handle(self, *args: Any, **options: Any) -> None:
        create_test_data()


def create_test_data() -> None:
    call_command("flush", "--noinput")

    User.objects.create_superuser("x", "x@admin.com", "x")
