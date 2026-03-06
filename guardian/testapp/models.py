import uuid

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AbstractBaseUser, AbstractUser
from django.db import models
from django.utils import timezone

from guardian.mixins import GuardianUserMixin
from guardian.models import (
    GroupObjectPermissionAbstract,
    GroupObjectPermissionBase,
    UserObjectPermissionBase,
)


class Post(models.Model):
    title = models.CharField("title", max_length=64)

    def __str__(self):
        return self.title


class DynamicAccessor:
    def __init__(self):
        pass

    def __getattr__(self, key):
        return DynamicAccessor()


class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey("Project", on_delete=models.CASCADE)


class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey("Project", on_delete=models.CASCADE)


class GenericGroupObjectPermission(GroupObjectPermissionAbstract):
    class Meta(GroupObjectPermissionAbstract.Meta):
        abstract = False


class Project(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        get_latest_by = "created_at"

    def __str__(self):
        return self.name


Project.not_a_relation_descriptor = DynamicAccessor()


# Simple model for testing inline admin functionality
class UserProfile(models.Model):
    """Simple model for testing inline admin functionality with Guardian permissions."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        # Ensure Django creates default permissions for this model
        default_permissions = ("add", "change", "delete", "view")

    def __str__(self):
        return f"Profile for {self.user.username}"


class MixedGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey("Mixed", on_delete=models.CASCADE)


class Mixed(models.Model):
    """
    Model for tests obj perms checks with generic user object permissions model
    and direct group object permissions model.
    """

    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class ReverseMixedUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey("ReverseMixed", on_delete=models.CASCADE)


class ReverseMixed(models.Model):
    """
    Model for tests obj perms checks with generic group object permissions model
    and generic group object permissions model.
    """

    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class LogEntryWithGroup(LogEntry):
    group = models.ForeignKey("auth.Group", null=True, blank=True, on_delete=models.CASCADE)

    objects = models.Manager()


class CharPKModel(models.Model):
    """
    Model for testing whether get_objects_for_user will work when the objects to
    be returned have varchar primary keys.
    """

    char_pk = models.CharField(primary_key=True, max_length=128)


class UUIDPKModel(models.Model):
    """
    Model for testing whether get_objects_for_user will work when the objects to
    be returned have UUID primary keys.
    """

    uuid_pk = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )


class CustomUser(AbstractUser, GuardianUserMixin):
    custom_id = models.AutoField(primary_key=True)


class CustomUsernameUser(AbstractBaseUser, GuardianUserMixin):
    email = models.EmailField(max_length=100, unique=True)
    USERNAME_FIELD = "email"

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email


class ParentTestModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)


class ChildTestModel(ParentTestModel):
    parent_id = models.OneToOneField(ParentTestModel, on_delete=models.CASCADE, parent_link=True)
    name = models.CharField(max_length=31)


class TextPKModel(models.Model):
    """
    Model for testing whether get_objects_for_user and get_objects_for_group
    will work when the objects have TextField primary keys.
    This simulates non-standard PK types like macaddr, inet, etc.
    """

    text_pk = models.TextField(primary_key=True)
