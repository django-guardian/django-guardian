# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import guardian.mixins
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0005_auto_20151217_2344'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUsernameUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('email', models.EmailField(unique=True, max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, guardian.mixins.GuardianUserMixin),
        )
    ]
