from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("guardian", "0003_remove_groupobjectpermission_guardian_gr_content_ae6aec_idx_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="groupobjectpermission",
            index=models.Index(fields=["content_type", "object_pk"], name="guardian_gr_content_ae6aec_idx"),
        ),
        migrations.AddIndex(
            model_name="userobjectpermission",
            index=models.Index(fields=["content_type", "object_pk"], name="guardian_us_content_179ed2_idx"),
        ),
    ]
