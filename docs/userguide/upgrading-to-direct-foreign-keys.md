---
title: Upgrading to Direct Foreign Keys
description: Step-by-step guide for upgrading existing projects from generic object permissions to direct foreign key based permissions while preserving all data.
---

# Upgrading to Direct Foreign Keys

This guide covers the process of migrating a **running, production project**
from django-guardian's default generic permission tables to the
[direct foreign key](performance.md#direct-foreign-keys) approach — without
losing any existing permission data.

## Why Migrate?

Django-guardian's default `UserObjectPermission` and `GroupObjectPermission`
models use Django's contenttypes framework to store a **generic relation**
(`content_type` + `object_pk`). This design is flexible, but it has a cost:

- `object_pk` is stored as a `CharField`, so every query must cast or compare
  strings instead of using native primary key types.
- There is no real database-level foreign key, meaning the database cannot
  enforce referential integrity or use foreign key indexes efficiently.
- As the permission tables grow, queries that filter by `content_type` and
  `object_pk` become increasingly expensive — especially on tables with
  millions of rows.

For **high-volume projects** — or any project where object permission checks
appear in hot paths — switching to direct foreign keys can yield a dramatic
improvement in query performance and data integrity.

!!! tip "See Also"
    [Performance Tuning — Direct Foreign Keys](performance.md#direct-foreign-keys)
    for an overview of the direct foreign key approach.

---

## Operational Safety

!!! danger "Do Not Run This Migration on a Live System"
    This migration **must not** run while the application is actively serving
    requests that create, modify, or delete object permissions. If a
    permission is assigned or removed in the generic table *during* the data
    copy, a **race condition** occurs: the new record will not be copied to
    the direct table, resulting in **silently lost permissions**.

Before starting the migration, complete **all three** of the following
pre-flight checks:

### 1. Enable Maintenance Mode

Take the application offline so that end users cannot trigger any permission
changes. A convenient way to do this is the
[django-maintenance-mode](https://github.com/fabiocaccamo/django-maintenance-mode)
package:

```bash
pip install django-maintenance-mode
python manage.py maintenance_mode on
```

### 2. Stop Background Workers

Stop or pause **all** Celery workers, cron jobs, management command schedules,
and any other background tasks that may call `assign_perm`, `remove_perm`, or
modify object permissions in any way. Any write to the generic permission
tables during the migration window can cause data inconsistency.

### 3. Take a Full Database Backup

Before touching any data, create a complete database backup. If anything goes
wrong during the migration, you need to be able to restore to the
pre-migration state.

```bash
# PostgreSQL example
pg_dump -Fc mydb > pre_direct_fk_migration.dump
```

---

## Step 1 — Define the Direct Foreign Key Models

For each model that has object permissions, create two new models that inherit
from `UserObjectPermissionBase` and `GroupObjectPermissionBase`. **Set
`enabled = False`** so that django-guardian continues to use the generic tables
while the new tables are being created and populated.

```python
# myapp/models.py

from django.db import models
from guardian.models import UserObjectPermissionBase, GroupObjectPermissionBase


class Project(models.Model):
    name = models.CharField(max_length=128, unique=True)

    class Meta:
        permissions = (
            ("view_project", "Can view project"),
            ("manage_project", "Can manage project"),
        )


class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="user_object_permissions"
    )
    enabled = False  # Keep using generic tables for now


class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="group_object_permissions"
    )
    enabled = False  # Keep using generic tables for now
```

Now generate and apply the migration to create the new tables:

```bash
python manage.py makemigrations myapp
python manage.py migrate myapp
```

At this point, the new tables exist but are empty, and django-guardian is
still reading from and writing to the generic tables.

---

## Step 2 — Data Migration

Create a data migration that copies every existing permission from the generic
tables into the new direct tables.

```bash
python manage.py makemigrations myapp --empty -n migrate_to_direct_fk
```

Then edit the generated file:

```python
# myapp/migrations/XXXX_migrate_to_direct_fk.py

from django.db import migrations


def forwards(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    UserObjectPermission = apps.get_model("guardian", "UserObjectPermission")
    GroupObjectPermission = apps.get_model("guardian", "GroupObjectPermission")

    Project = apps.get_model("myapp", "Project")
    ProjectUserObjPerm = apps.get_model("myapp", "ProjectUserObjectPermission")
    ProjectGroupObjPerm = apps.get_model("myapp", "ProjectGroupObjectPermission")

    project_ct = ContentType.objects.get_for_model(Project)

    # --- User permissions ---
    user_perms = UserObjectPermission.objects.filter(content_type=project_ct)

    BATCH_SIZE = 2000
    batch = []
    for perm in user_perms.iterator():
        batch.append(
            ProjectUserObjPerm(
                permission_id=perm.permission_id,
                user_id=perm.user_id,
                # Cast object_pk to the target model's PK type.
                content_object_id=int(perm.object_pk),  # see warning below
            )
        )
        if len(batch) >= BATCH_SIZE:
            ProjectUserObjPerm.objects.bulk_create(batch, ignore_conflicts=True)
            batch = []

    if batch:
        ProjectUserObjPerm.objects.bulk_create(batch, ignore_conflicts=True)

    # --- Group permissions ---
    group_perms = GroupObjectPermission.objects.filter(content_type=project_ct)

    batch = []
    for perm in group_perms.iterator():
        batch.append(
            ProjectGroupObjPerm(
                permission_id=perm.permission_id,
                group_id=perm.group_id,
                content_object_id=int(perm.object_pk),  # see warning below
            )
        )
        if len(batch) >= BATCH_SIZE:
            ProjectGroupObjPerm.objects.bulk_create(batch, ignore_conflicts=True)
            batch = []

    if batch:
        ProjectGroupObjPerm.objects.bulk_create(batch, ignore_conflicts=True)


def backwards(apps, schema_editor):
    """
    Reverse migration: remove all records from direct tables.
    The generic table records are still intact.
    """
    ProjectUserObjPerm = apps.get_model("myapp", "ProjectUserObjectPermission")
    ProjectGroupObjPerm = apps.get_model("myapp", "ProjectGroupObjectPermission")
    ProjectUserObjPerm.objects.all().delete()
    ProjectGroupObjPerm.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "XXXX_previous_migration"),  # replace with actual name
        ("guardian", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
```

!!! warning "Primary Key Type Casting"
    The generic table stores `object_pk` as a **string**. You must cast it to
    the target model's actual primary key type when building the direct
    record:

    | Target PK type | Cast |
    |---|---|
    | `AutoField` / `BigAutoField` / `IntegerField` | `int(perm.object_pk)` |
    | `UUIDField` | `uuid.UUID(perm.object_pk)` |
    | `CharField` | No cast needed — use `perm.object_pk` directly |

    Mismatched types will cause `IntegrityError` or silent data corruption.

!!! tip "Multiple Models"
    If you have more than one model with object permissions (e.g. `Project`,
    `Task`, `Document`), you need to repeat the direct model pair and the
    migration block **for each model**. You can place all copies in the same
    `RunPython` function to run them in a single migration.

Apply the migration:

```bash
python manage.py migrate myapp
```

---

## Step 3 — Enable the Direct Models

Now that the data is in place, remove the `enabled = False` flag (or set it to
`True`) so that django-guardian starts using the direct tables for all future
reads and writes:

```python
# myapp/models.py

class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="user_object_permissions"
    )
    # enabled = False  ← removed


class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="group_object_permissions"
    )
    # enabled = False  ← removed
```

Since `enabled` is a **class attribute** and not a database field, no new
migration is required. A deployment (application restart) is enough for the
change to take effect.

!!! success "Verification"
    After enabling, verify that permissions still work correctly:

    ```python
    from guardian.shortcuts import get_perms
    from myapp.models import Project

    project = Project.objects.first()
    print(get_perms(user, project))
    ```

    The output should match the permissions that were previously assigned
    via the generic tables.

At this point you can disable maintenance mode and resume normal operations:

```bash
python manage.py maintenance_mode off
```

---

## Step 4 — Clean Up Generic Records

After the migration is verified and the direct tables are actively in use, the
old generic records for the migrated models are **no longer read** by
django-guardian. However, they still occupy space in the database. Leaving them
in place has two negative consequences:

1. **Database bloat.** The `guardian_userobjectpermission` and
   `guardian_groupobjectpermission` tables retain rows that are never queried,
   wasting storage and slowing down maintenance operations like `VACUUM` or
   index rebuilds.

2. **Stale data risk.** If the `enabled = False` flag is accidentally
   reintroduced (e.g. during a merge conflict), django-guardian will fall back
   to reading the generic tables. Those records are now **stale** — they do
   not reflect permission changes made after the migration — and will produce
   incorrect authorization decisions that are extremely hard to debug.

!!! danger "Important"
    It is **strongly recommended** to delete the orphaned generic records once
    you are confident the direct foreign key setup is working correctly.

Create a dedicated cleanup migration:

```python
# myapp/migrations/XXXX_cleanup_generic_perms.py

from django.db import migrations


def cleanup_generic_records(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    UserObjectPermission = apps.get_model("guardian", "UserObjectPermission")
    GroupObjectPermission = apps.get_model("guardian", "GroupObjectPermission")

    Project = apps.get_model("myapp", "Project")
    project_ct = ContentType.objects.get_for_model(Project)

    UserObjectPermission.objects.filter(content_type=project_ct).delete()
    GroupObjectPermission.objects.filter(content_type=project_ct).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "XXXX_migrate_to_direct_fk"),  # replace with actual name
        ("guardian", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(cleanup_generic_records, migrations.RunPython.noop),
    ]
```

!!! tip
    If you are not comfortable with an irreversible cleanup, keep a
    database backup taken **after Step 2** as your rollback safety net.

---

## Quick Reference

| Step | Action | Downtime Required |
|---|---|---|
| **Prep** | Backup database, enable maintenance mode | Yes |
| **1** | Define direct FK models with `enabled = False`, run `makemigrations` + `migrate` | No (schema only) |
| **2** | Data migration — copy generic → direct with `bulk_create` | Yes |
| **3** | Remove `enabled = False`, deploy | No (app restart) |
| **4** | Delete stale generic records | No |
| **Post** | Disable maintenance mode, verify | — |
