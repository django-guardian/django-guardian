from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('admin', '0001_initial'),
        ('testapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntryWithGroup',
            fields=[
                ('logentry_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='admin.LogEntry')),
                ('group', models.ForeignKey(blank=True, to='auth.Group', null=True)),
            ],
            options={
            },
            bases=('admin.logentry',),
        ),
    ]