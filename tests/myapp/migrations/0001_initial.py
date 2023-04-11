# Generated by Django 4.1.1 on 2022-11-05 16:54

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Thing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nested", models.JSONField(default=dict)),
                ("array", models.JSONField(default=list)),
                ("dict", models.JSONField(default=dict)),
            ],
        ),
    ]
