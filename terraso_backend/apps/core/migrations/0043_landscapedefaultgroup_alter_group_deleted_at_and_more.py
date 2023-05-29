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

# Generated by Django 4.2.1 on 2023-05-18 16:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.core.models.commons


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0042_landscapedefaultgroup_group_enroll_method_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="landscape",
            name="taxonomy_terms",
            field=models.ManyToManyField(blank=True, to="core.taxonomyterm"),
        ),
    ]