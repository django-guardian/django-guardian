---
title: Entity Roles with Groups
description: A common pattern for modeling per-entity roles using groups and object permissions.
---

# Entity Roles with Groups

When users can have different roles per entity (for example a user is a teacher in one school and a student in another), a common pattern is to model those roles with groups and assign object permissions to those groups.

This avoids content type mismatches and works well with how django-guardian validates object permissions.

## Why this pattern

`BaseObjectPermission` and `ObjectPermissionBackend` enforce that a permission and object must have compatible content types.

For example, assigning an `auth` group permission (like `view_group`) to a `School` instance is invalid because the permission is defined for the `Group` model, not for `School`.

Instead, define permissions for the target model (or related models) and grant those permissions to role groups.

## Step 1: Create per-entity role groups

Create one group per role for each entity instance.

Option A — import the model directly (simplest):

```python
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from schools.models import School  # import the actual class


@receiver(post_save, sender=School)
def ensure_school_role_groups(sender, instance, created, **kwargs):
    if not created:
        return

    # Keep names deterministic so they can be looked up later.
    Group.objects.get_or_create(name=f"{instance.slug}-teachers")
    Group.objects.get_or_create(name=f"{instance.slug}-students")
```

Option B — connect in `AppConfig.ready()` to avoid circular imports:

```python
# schools/apps.py
from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    name = "schools"

    def ready(self):
        from django.contrib.auth.models import Group
        from django.db.models.signals import post_save

        School = self.get_model("School")

        def ensure_school_role_groups(sender, instance, created, **kwargs):
            if not created:
                return
            Group.objects.get_or_create(name=f"{instance.slug}-teachers")
            Group.objects.get_or_create(name=f"{instance.slug}-students")

        # weak=False prevents the nested function from being garbage-collected.
        post_save.connect(ensure_school_role_groups, sender=School, weak=False)
```

!!! note

    Django model signals such as `post_save` **do** support string senders in
    the `"app_label.ModelName"` form, so `sender="schools.School"` can work.
    That said, using the actual model class (or connecting the signal in
    `AppConfig.ready()`) is often clearer and easier to follow when reading the
    code, especially in larger projects.

## Step 2: Add users to the correct role groups

Put each user into the group that represents their role for that specific entity.

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

user_a = get_user_model().objects.get(username="user_a")
user_b = get_user_model().objects.get(username="user_b")
teachers_group = Group.objects.get(name="school-a-teachers")
students_group = Group.objects.get(name="school-a-students")

teachers_group.user_set.add(user_a)
students_group.user_set.add(user_b)
```

A user can belong to multiple groups, so the same teacher can be in `school-a-teachers` and `school-b-teachers`.

## Step 3: Assign object permissions to those groups

Assign permissions whose content type matches the protected object.

```python
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm

school_a_teachers = Group.objects.get(name="school-a-teachers")
school_b_teachers = Group.objects.get(name="school-b-teachers")
school_a = ...  # School instance
school_b = ...  # School instance

assign_perm("add_homework", school_a_teachers, school_a)
assign_perm("add_notification", school_b_teachers, school_b)
```

In this setup, users inherit effective permissions from membership:

- members of `school-a-teachers` can add homework in `school_a`
- members of `school-b-teachers` can add notifications in `school_b`

## Step 4: Check effective permissions in application code

Use standard permission checks; group-derived permissions are included.

```python
from django.contrib.auth import get_user_model

user_a = get_user_model().objects.get(username="user_a")
school_a = ...  # School instance
school_b = ...  # School instance

user_a.has_perm("add_homework", school_a)      # True
user_a.has_perm("add_homework", school_b)      # False
user_a.has_perm("add_notification", school_b)  # True
```

You can also filter accessible objects with `get_objects_for_user` when building list views or APIs.

## Notes and trade-offs

- This pattern scales well when roles are scoped to an entity.
- Group names should be deterministic and unique (slugs are usually a good base).
- If your project needs a custom group type, see `custom-group-model`.
- For assignment and check APIs, see `assign` and `checks`.
