# Generated by Django 4.1 on 2022-10-20 18:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_remove_landscape_area_type_landscape_area_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="landscape",
            name="development_strategy",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.landscapedevelopmentstrategy",
            ),
        ),
        migrations.AlterField(
            model_name="landscape",
            name="population",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
