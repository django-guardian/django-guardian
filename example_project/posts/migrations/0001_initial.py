from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=64, verbose_name=b'title')),
                ('slug', models.SlugField(max_length=64)),
                ('content', models.TextField(verbose_name=b'content')),
                ('created_at', models.DateTimeField(
                    auto_now_add=True, db_index=True)),
            ],
            options={
                'get_latest_by': 'created_at',
                'default_permissions': ('add', 'change', 'delete'),
                'permissions': (('view_post', 'Can view post'),),
            },
        ),
    ]
