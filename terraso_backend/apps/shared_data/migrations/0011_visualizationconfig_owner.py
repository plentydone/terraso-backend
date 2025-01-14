# Copyright © 2023 Technology Matters
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see https://www.gnu.org/licenses/.


# Generated by Django 4.2.6 on 2023-10-13 22:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def group_to_owner(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    VisualizationConfig = apps.get_model("shared_data", "VisualizationConfig")
    LandscapeGroup = apps.get_model("core", "LandscapeGroup")
    configs = VisualizationConfig.objects.all()
    for config in configs:
        group = config.group
        landscape_group = LandscapeGroup.objects.filter(
            group=group, is_default_landscape_group=True
        ).first()
        if landscape_group is None:
            config.owner_content_type = ContentType.objects.get_for_model(config.group)
            config.owner_object_id = config.group.id
        else:
            config.owner_content_type = ContentType.objects.get_for_model(landscape_group.landscape)
            config.owner_object_id = landscape_group.landscape.id
        config.save()


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0046_shared_resource"),
        ("shared_data", "0010_visualizationconfig_mapbox_tileset_id_status"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="visualizationconfig",
            name="shared_data_visualizationconfig_unique_active_slug_by_group",
        ),
        migrations.AddField(
            model_name="visualizationconfig",
            name="owner_content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owner_content_type",
                to="contenttypes.contenttype",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="visualizationconfig",
            name="owner_object_id",
            field=models.UUIDField(null=True),
        ),
        migrations.RunPython(group_to_owner),
        migrations.AddConstraint(
            model_name="visualizationconfig",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("owner_object_id", "slug"),
                name="shared_data_visualizationconfig_unique_active_slug_by_group",
            ),
        ),
    ]
