from django.db import models


class Thing(models.Model):

    nested = models.JSONField(default=dict)
    array = models.JSONField(default=list)

    def __str__(self):
        return str(self.id)
