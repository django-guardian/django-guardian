from unittest import mock
import warnings

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from guardian.managers import GroupObjectPermissionManager, UserObjectPermissionManager
from guardian.utils import get_group_obj_perms_model, get_user_obj_perms_model

User = get_user_model()


class TestManagers(TestCase):
    def test_user_manager_assign(self):
        manager = UserObjectPermissionManager()
        manager.assign_perm = mock.Mock()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            manager.assign("perm", "user", "object")

        manager.assign_perm.assert_called_once_with("perm", "user", "object")

        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn(
            "UserObjectPermissionManager method 'assign' is being renamed to 'assign_perm'.", str(w[0].message)
        )

    def test_group_manager_assign(self):
        manager = GroupObjectPermissionManager()
        manager.assign_perm = mock.Mock()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            manager.assign("perm", "group", "object")

        manager.assign_perm.assert_called_once_with("perm", "group", "object")

        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn(
            "UserObjectPermissionManager method 'assign' is being renamed to 'assign_perm'.", str(w[0].message)
        )


class TestManagerAssignPerm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.group = Group.objects.create(name="testgroup")
        self.obj = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.content_type = ContentType.objects.get_for_model(self.obj)
        self.permission = Permission.objects.get(content_type=self.content_type, codename="change_contenttype")

    def test_user_assign_perm(self):
        UserObjectPermission = get_user_obj_perms_model(self.obj)
        with self.assertNumQueries(5):
            UserObjectPermission.objects.assign_perm(self.permission, self.user, self.obj)

    def test_user_bulk_assign_perm(self):
        UserObjectPermission = get_user_obj_perms_model(self.obj)
        with self.assertNumQueries(3):
            UserObjectPermission.objects.bulk_assign_perm(self.permission, self.user, [self.obj])

    def test_user_assign_perm_to_many(self):
        UserObjectPermission = get_user_obj_perms_model(self.obj)
        with self.assertNumQueries(1):
            UserObjectPermission.objects.assign_perm_to_many(self.permission, [self.user], self.obj)

    def test_group_assign_perm(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(5):
            GroupObjectPermission.objects.assign_perm(self.permission, self.group, self.obj)

    def test_group_bulk_assign_perm(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(2):
            GroupObjectPermission.objects.bulk_assign_perm(self.permission, self.group, [self.obj])

    def test_group_assign_perm_to_many(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(1):
            GroupObjectPermission.objects.assign_perm_to_many(self.permission, [self.group], self.obj)
