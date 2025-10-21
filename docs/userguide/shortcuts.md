---
title: Shortcuts
description: Understanding permission query functions and their relationships.
---

# Permission Query Functions

Django Guardian provides several shortcut functions for querying permissions. Understanding their relationships and differences is crucial for proper usage.

## Permission Query Functions Overview

When working with object permissions in django-guardian, there are three main functions for querying permissions:

### Function Relationships

- **`get_perms(user, obj)`**: Returns ALL permissions (user + group permissions combined)
- **`get_user_perms(user, obj)`**: Returns ONLY direct user permissions
- **`get_group_perms(user, obj)`**: Returns ONLY group permissions

For any user and object: `get_perms(user, obj) = get_user_perms(user, obj) + get_group_perms(user, obj)`

### Key Differences

| Function | Returns | Type | Includes Groups | Use Case |
|----------|---------|------|----------------|----------|
| `get_perms()` | All permissions | `list[str]` | Yes | General permission checking |
| `get_user_perms()` | Direct user permissions only | `QuerySet` | No | Permission management interfaces |
| `get_group_perms()` | Group permissions only | `QuerySet` | N/A | Understanding permission inheritance |

## Important Notes

- **Inactive users** (`is_active=False`): All functions return empty results
- **Return types**: `get_perms()` returns a list, while `get_user_perms()` and `get_group_perms()` return QuerySets
- **Group behavior**: When `get_group_perms()` is called with a user, it returns permissions from ALL groups the user belongs to
- **Superusers**: `get_perms()` returns all available permissions for the object's model

## Common Use Cases

### General Permission Checking

Use `get_perms()` when you need to check if a user has a specific permission, regardless of whether it comes from direct assignment or group membership:

```python
from guardian.shortcuts import get_perms

user_perms = get_perms(user, article)
if 'change_article' in user_perms:
    # User can change this article (either directly or through groups)
    allow_editing = True
```

### Permission Management Interfaces

Use `get_user_perms()` and `get_group_perms()` when building interfaces that show the source of permissions:

```python
from guardian.shortcuts import get_user_perms, get_group_perms

# Show user what permissions they have directly
direct_perms = get_user_perms(user, article)

# Show user what permissions they have through groups
group_perms = get_group_perms(user, article)

# Display in UI: "You have 'edit' permission directly, and 'delete' through the 'Editors' group"
```

### Permission Auditing

Use individual functions to understand permission inheritance:

```python
from guardian.shortcuts import get_perms, get_user_perms, get_group_perms

all_perms = get_perms(user, document)
direct_perms = list(get_user_perms(user, document).values_list('codename', flat=True))
group_perms = list(get_group_perms(user, document).values_list('codename', flat=True))

print(f"All permissions: {all_perms}")
print(f"Direct permissions: {direct_perms}")
print(f"Group permissions: {group_perms}")
```

### Selective Permission Removal

Use `get_user_perms()` when you need to remove only direct permissions without affecting group permissions:

```python
from guardian.shortcuts import get_user_perms, remove_perm

# Remove only direct user permissions, keep group permissions intact
direct_perms = get_user_perms(user, article)
for perm in direct_perms:
    remove_perm(perm.codename, user, article)
```

## Common Pitfalls

!!! warning "Don't Confuse get_user_perms() with get_perms()"

    Many developers expect `get_user_perms()` to return the same results as `get_perms()`, but this is incorrect:

    ```python
    # This user has permissions through group membership only
    user.groups.add(editors_group)  # editors_group has 'change_article' permission

    get_perms(user, article)      # Returns: ['change_article']
    get_user_perms(user, article) # Returns: [] (empty - no direct permissions)
    ```

!!! tip "Use get_perms() for Most Cases"

    Unless you specifically need to distinguish between direct and inherited permissions, use `get_perms()` for general permission checking.

## Examples

### Basic Usage

```python
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm, get_perms, get_user_perms, get_group_perms
from myapp.models import Article

user = User.objects.get(username='john')
article = Article.objects.get(pk=1)

# Assign direct permission
assign_perm('change_article', user, article)

# Check all permissions (includes direct + group)
all_perms = get_perms(user, article)  # ['change_article']

# Check only direct permissions
direct_perms = get_user_perms(user, article)  # QuerySet with 'change_article'

# Check only group permissions
group_perms = get_group_perms(user, article)  # Empty QuerySet
```

### Group Permissions Example

```python
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm, get_perms, get_user_perms, get_group_perms

user = User.objects.get(username='jane')
group = Group.objects.create(name='editors')
article = Article.objects.get(pk=1)

# Add user to group and assign group permission
user.groups.add(group)
assign_perm('delete_article', group, article)

# Now check permissions
all_perms = get_perms(user, article)        # ['delete_article']
direct_perms = get_user_perms(user, article) # Empty QuerySet
group_perms = get_group_perms(user, article)  # QuerySet with 'delete_article'
```

### Mixed Permissions Example

```python
# User has both direct and group permissions
assign_perm('change_article', user, article)  # Direct permission
assign_perm('delete_article', group, article) # Group permission (user is in group)

all_perms = get_perms(user, article)        # ['change_article', 'delete_article']
direct_perms = get_user_perms(user, article) # QuerySet with 'change_article'
group_perms = get_group_perms(user, article)  # QuerySet with 'delete_article'
```
