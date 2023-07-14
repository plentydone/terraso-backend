# Generated by Django 4.2.3 on 2023-07-11 22:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("project_management", "0012_make_projectsettings_not_null"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="site",
            name="created_by",
        ),
        migrations.AddField(
            model_name="project",
            name="description",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]