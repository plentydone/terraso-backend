# Generated by Django 4.1.7 on 2023-03-29 21:19

import uuid

import rules.contrib.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Site",
            fields=[
                ("deleted_at", models.DateTimeField(db_index=True, editable=False, null=True)),
                ("deleted_by_cascade", models.BooleanField(default=False, editable=False)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(blank=True, editable=False, max_length=250)),
                ("name", models.CharField(max_length=200)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
            ],
            options={
                "ordering": ["created_at"],
                "get_latest_by": "-created_at",
                "abstract": False,
            },
            bases=(rules.contrib.models.RulesModelMixin, models.Model),
        ),
        migrations.AddConstraint(
            model_name="site",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("slug",),
                name="project_management_site_unique_active_slug",
                violation_error_message="slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="site",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("name",),
                name="project_management_site_unique_active_name",
                violation_error_message="name",
            ),
        ),
    ]
