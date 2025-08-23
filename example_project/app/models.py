from __future__ import annotations

from django.db import models


class Thing(models.Model):
    nested = models.JSONField(default=dict)
    array = models.JSONField(default=list)
    dict = models.JSONField(default=dict)
    required = models.JSONField()

    def __str__(self) -> str:
        return str(self.id)
