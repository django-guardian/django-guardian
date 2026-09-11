# Generated migration for TextPKModel

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("testapp", "0009_userprofile"),
    ]

    operations = [
        migrations.CreateModel(
            name="TextPKModel",
            fields=[
                ("text_pk", models.TextField(primary_key=True, serialize=False)),
            ],
        ),
    ]
