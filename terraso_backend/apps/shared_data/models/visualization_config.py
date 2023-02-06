# Copyright © 2021-2023 Technology Matters
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

from django.db import models

from apps.core.models import BaseModel, Group, SlugModel, User
from apps.core.models.commons import validate_name
from apps.shared_data import permission_rules as perm_rules

from .data_entries import DataEntry


class VisualizationConfig(SlugModel):
    title = models.CharField(max_length=128, validators=[validate_name])
    configuration = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="created_visualization_configs",
    )
    data_entry = models.ForeignKey(
        DataEntry, on_delete=models.CASCADE, related_name="visualizations"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="visualizations")

    field_to_slug = "title"

    class Meta(BaseModel.Meta):
        constraints = (
            models.UniqueConstraint(
                fields=("group_id", "slug"),
                condition=models.Q(deleted_at__isnull=True),
                name="shared_data_visualizationconfig_unique_active_slug_by_group",
            ),
        )
        verbose_name_plural = "Visualization Configs"
        rules_permissions = {
            "change": perm_rules.allowed_to_change_visualization_config,
            "delete": perm_rules.allowed_to_delete_visualization_config,
            "view": perm_rules.allowed_to_view_visualization_config,
        }