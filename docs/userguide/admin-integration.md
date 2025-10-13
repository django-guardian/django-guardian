---
title: Admin
description: How to use django-guardian with Django's admin interface.
---

# Django Admin Integration

Django comes with an excellent and widely used *Admin* application.
Basically, it provides content management for Django applications.
Users with access to admin panel can manage users, groups, permissions and
other data provided by system.

`django-guardian` comes with simple object permissions management
integration for Django's admin application.

## Usage

It is easy to use admin integration. Simply use `GuardedModelAdmin` instead of standard
`django.contrib.admin.ModelAdmin` class for registering models within
the admin. In example, look at the following model:

``` python
from django.db import models


class Post(models.Model):
    title = models.CharField('title', max_length=64)
    slug = models.SlugField(max_length=64)
    content = models.TextField('content')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        permissions = (
            ('hide_post', 'Can hide post'),
        )
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return {'post_slug': self.slug}
```

We want to register `Post` model within admin application. Normally, we
would do this as follows within `admin.py` file of our application:

``` python
from django.contrib import admin

from posts.models import Post


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ('title', 'slug', 'created_at')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Post, PostAdmin)
```

If we would like to add object permissions management for `Post` model
we would need to change `PostAdmin` base class into `GuardedModelAdmin`.
Our code could look as follows:

``` python
from django.contrib import admin

from posts.models import Post

from guardian.admin import GuardedModelAdmin


class PostAdmin(GuardedModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ('title', 'slug', 'created_at')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Post, PostAdmin)
```

And thats it. We can now navigate to **change** post page and just next
to the *history* link we can click *Object permissions* button to manage
row level permissions.

!!! note
    Example above is shipped with `django-guardian` package with the example project.

## Inline Admin Support

Django admin provides inline functionality that allows editing related objects
on the same page as a parent object. `django-guardian` supports inline admin
forms through the `GuardedInlineAdminMixin` class.

### Using GuardedInlineAdminMixin

To use inline admin forms with Guardian permissions, you need to inherit from
`GuardedInlineAdminMixin` along with Django's inline admin classes. Here's an
example with a `User` and `UserPhone` relationship:

``` python
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User

from guardian.admin import GuardedModelAdmin, GuardedInlineAdminMixin


# Example models
class UserPhone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    phone_number = models.CharField(max_length=20)
    phone_type = models.CharField(max_length=10, choices=[
        ('mobile', 'Mobile'),
        ('home', 'Home'),
        ('work', 'Work')
    ])

    class Meta:
        permissions = [
            ('view_userphone', 'Can view user phone'),
            ('add_userphone', 'Can add user phone'),
            ('change_userphone', 'Can change user phone'),
            ('delete_userphone', 'Can delete user phone'),
        ]


# Inline admin class
class UserPhoneInline(GuardedInlineAdminMixin, admin.StackedInline):
    model = UserPhone
    extra = 1


# Main admin class
class UserAdmin(GuardedModelAdmin):
    inlines = [UserPhoneInline]
    list_display = ('username', 'first_name', 'last_name', 'email')

admin.site.register(User, UserAdmin)
```

### How It Works

The `GuardedInlineAdminMixin` provides the necessary permission checking methods
that Django's inline admin forms expect:

- `has_add_permission(request, obj=None)` - Check if user can add inline objects
- `has_view_permission(request, obj=None)` - Check if user can view inline objects
- `has_change_permission(request, obj=None)` - Check if user can change inline objects
- `has_delete_permission(request, obj=None)` - Check if user can delete inline objects

These methods integrate with Guardian's object-level permissions system. When `obj`
is provided, they check for object-level permissions. When `obj` is `None`, they
check for global permissions.

### Supported Inline Types

The mixin works with both types of Django admin inline classes:

``` python
# StackedInline example
class UserPhoneInline(GuardedInlineAdminMixin, admin.StackedInline):
    model = UserPhone
    extra = 1

# TabularInline example
class UserPhoneTabularInline(GuardedInlineAdminMixin, admin.TabularInline):
    model = UserPhone
    extra = 0
```

### Permission Behavior

- **Superusers**: Have all permissions automatically granted
- **Global permissions**: When no specific object is provided, checks global model permissions
- **Object-level permissions**: When a parent object is provided, checks permissions on that specific object
- **Permission isolation**: Users only see inline forms for objects they have appropriate permissions for

!!! tip
    The inline permission checks are performed in the context of the parent object.
    This means users need permissions on the inline model type, and the permission
    checks can be scoped to the specific parent object being edited.

!!! warning
    Make sure to define appropriate permissions in your inline model's `Meta.permissions`
    if you want to use custom permissions beyond Django's default add, change, delete, and view.
