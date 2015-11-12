# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0002_logentrywithgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='NonIntPKModel',
            fields=[
                ('char_pk', models.CharField(max_length=128, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username.', 'invalid')]),
            preserve_default=True,
        ),
    ]
