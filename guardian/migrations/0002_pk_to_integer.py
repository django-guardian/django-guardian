# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guardian', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupobjectpermission',
            name='object_pk',
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='userobjectpermission',
            name='object_pk',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
