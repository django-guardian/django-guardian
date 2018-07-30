# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guardian', '0001_initial'),
    ]

    operations = [
        # default migration does not include 'using object_pk::integer' so thats why we have custom migration
        migrations.RunSQL("alter table guardian_userobjectpermission alter column object_pk type integer using object_pk::integer;"),
        migrations.RunSQL("alter table guardian_groupobjectpermission alter column object_pk type integer using object_pk::integer;"),
    ]
