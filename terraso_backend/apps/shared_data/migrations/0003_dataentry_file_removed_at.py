# Generated by Django 4.0.4 on 2022-05-31 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shared_data", "0002_dataentry_size"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataentry",
            name="file_removed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]