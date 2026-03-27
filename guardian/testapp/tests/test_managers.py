from unittest import mock
import warnings

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from guardian.managers import (
    GroupObjectPermissionManager,
    UserObjectPermissionManager,
    _is_using_default_content_type,
)
from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.testapp.models import ChildTestModel, ParentTestModel
from guardian.utils import get_group_obj_perms_model, get_user_obj_perms_model

User = get_user_model()


def get_parent_content_type(obj):
    """
    Custom GET_CONTENT_TYPE function simulating polymorphic model libraries
    (e.g. django-polymorphic). Returns ParentTestModel's ContentType for
    ChildTestModel instances instead of the concrete model's ContentType.
    Used as the GUARDIAN_GET_CONTENT_TYPE target in regression tests.
    """
    if isinstance(obj, ChildTestModel):
        return ContentType.objects.get_for_model(ParentTestModel)
    return ContentType.objects.get_for_model(obj)


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
            assigned = UserObjectPermission.objects.assign_perm(self.permission, self.user, self.obj)
        self.assertEqual(assigned, UserObjectPermission.objects.get(user=self.user, permission=self.permission))

    def test_user_bulk_assign_perm(self):
        UserObjectPermission = get_user_obj_perms_model(self.obj)
        with self.assertNumQueries(3):
            assigned = UserObjectPermission.objects.bulk_assign_perm(self.permission, self.user, [self.obj])
        self.assertEqual(assigned, [UserObjectPermission.objects.get(user=self.user, permission=self.permission)])

    def test_user_bulk_assign_perm_empty_list(self):
        UserObjectPermission = get_user_obj_perms_model(self.obj)
        with self.assertNumQueries(0):
            assigned = UserObjectPermission.objects.bulk_assign_perm(self.permission, self.user, [])
        self.assertEqual(assigned, [])

    def test_user_assign_perm_to_many(self):
        UserObjectPermission = get_user_obj_perms_model(self.obj)
        with self.assertNumQueries(1):
            assigned = UserObjectPermission.objects.assign_perm_to_many(self.permission, [self.user], self.obj)
        self.assertEqual(assigned, [UserObjectPermission.objects.get(user=self.user, permission=self.permission)])

    def test_group_assign_perm(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(5):
            assigned = GroupObjectPermission.objects.assign_perm(self.permission, self.group, self.obj)
        self.assertEqual(assigned, GroupObjectPermission.objects.get(group=self.group, permission=self.permission))

    def test_group_bulk_assign_perm(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(2):
            assigned = GroupObjectPermission.objects.bulk_assign_perm(self.permission, self.group, [self.obj])
        self.assertEqual(assigned, [GroupObjectPermission.objects.get(group=self.group, permission=self.permission)])

    def test_group_bulk_assign_perm_empty_list(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(0):
            assigned = GroupObjectPermission.objects.bulk_assign_perm(self.permission, self.group, [])
        self.assertEqual(assigned, [])

    def test_group_assign_perm_to_many(self):
        GroupObjectPermission = get_group_obj_perms_model(self.obj)
        with self.assertNumQueries(1):
            assigned = GroupObjectPermission.objects.assign_perm_to_many(self.permission, [self.group], self.obj)
        self.assertEqual(assigned, [GroupObjectPermission.objects.get(group=self.group, permission=self.permission)])


class TestAssignPermCustomContentType(TestCase):
    """
    Regression tests for the bug introduced in 3.3.0 where adding
    ``defaults={"content_object": obj}`` to the ``get_or_create`` call in
    ``assign_perm`` caused ``GenericForeignKey.__set__`` to silently overwrite
    the ``content_type`` that was set by a custom ``GUARDIAN_GET_CONTENT_TYPE``
    function with the object's own concrete ``ContentType``.

    The ``GUARDIAN_GET_CONTENT_TYPE`` setting is authoritative; whatever
    content type it returns must be the one persisted on the permission row.
    This matters for polymorphic model setups where the custom function
    deliberately returns a base/proxy content type instead of the concrete one.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser_ctype")
        self.group = Group.objects.create(name="testgroup_ctype")
        self.child = ChildTestModel.objects.create(name="polymorphic child")
        self.parent_ctype = ContentType.objects.get_for_model(ParentTestModel)
        self.child_ctype = ContentType.objects.get_for_model(ChildTestModel)
        # Sanity: the two content types must differ for these tests to be meaningful.
        self.assertNotEqual(self.parent_ctype, self.child_ctype)

    def test_assign_perm_user_uses_custom_content_type(self):
        """
        UserObjectPermission.assign_perm must store the content_type returned
        by GUARDIAN_GET_CONTENT_TYPE, not the content_type derived from the
        GenericForeignKey assignment introduced by defaults={"content_object": obj}.
        """
        with mock.patch(
            "guardian.conf.settings.GET_CONTENT_TYPE",
            "guardian.testapp.tests.test_managers.get_parent_content_type",
        ):
            obj_perm = UserObjectPermission.objects.assign_perm("change_parenttestmodel", self.user, self.child)

        self.assertEqual(
            obj_perm.content_type,
            self.parent_ctype,
            "assign_perm ignored GUARDIAN_GET_CONTENT_TYPE: content_type was overwritten "
            "by GenericForeignKey.__set__ via defaults={'content_object': obj}",
        )
        self.assertNotEqual(obj_perm.content_type, self.child_ctype)

    def test_assign_perm_group_uses_custom_content_type(self):
        """
        GroupObjectPermission.assign_perm must store the content_type returned
        by GUARDIAN_GET_CONTENT_TYPE, not the content_type derived from the
        GenericForeignKey assignment introduced by defaults={"content_object": obj}.
        """
        with mock.patch(
            "guardian.conf.settings.GET_CONTENT_TYPE",
            "guardian.testapp.tests.test_managers.get_parent_content_type",
        ):
            obj_perm = GroupObjectPermission.objects.assign_perm("change_parenttestmodel", self.group, self.child)

        self.assertEqual(
            obj_perm.content_type,
            self.parent_ctype,
            "assign_perm ignored GUARDIAN_GET_CONTENT_TYPE: content_type was overwritten "
            "by GenericForeignKey.__set__ via defaults={'content_object': obj}",
        )
        self.assertNotEqual(obj_perm.content_type, self.child_ctype)


class TestIsUsingDefaultContentType(TestCase):
    """
    Unit tests for the _is_using_default_content_type helper function.

    This function determines whether the GUARDIAN_GET_CONTENT_TYPE setting
    points to the default get_default_content_type function or a custom one.
    This is critical for avoiding the GenericForeignKey content_type overwrite bug.
    """

    def test_returns_true_for_default_content_type(self):
        """Should return True when using the default content type function."""
        # Default setting should point to guardian.ctypes.get_default_content_type
        with mock.patch("guardian.conf.settings.GET_CONTENT_TYPE", "guardian.ctypes.get_default_content_type"):
            self.assertTrue(_is_using_default_content_type())

    def test_returns_false_for_custom_content_type(self):
        """Should return False when using a custom content type function."""
        with mock.patch(
            "guardian.conf.settings.GET_CONTENT_TYPE",
            "guardian.testapp.tests.test_managers.get_parent_content_type",
        ):
            self.assertFalse(_is_using_default_content_type())

    def test_returns_false_for_any_non_default_path(self):
        """Should return False for any setting value that doesn't equal the default path."""
        for path in [
            "nonexistent.module.function",
            "fake_module.fake_function",
            "guardian.ctypes.nonexistent_function",
        ]:
            with mock.patch("guardian.conf.settings.GET_CONTENT_TYPE", path):
                self.assertFalse(_is_using_default_content_type())

    def test_string_comparison(self):
        """Should compare the setting string directly against the default dotted path."""
        with mock.patch("guardian.conf.settings.GET_CONTENT_TYPE", "guardian.ctypes.get_default_content_type"):
            result = _is_using_default_content_type()
            self.assertTrue(result, "Default path string should be recognized")

    def test_not_cached_allows_dynamic_changes(self):
        """
        The function should not cache results to allow mock.patch during tests.
        Each call should re-evaluate the setting.
        """
        # First call with default
        with mock.patch("guardian.conf.settings.GET_CONTENT_TYPE", "guardian.ctypes.get_default_content_type"):
            first_result = _is_using_default_content_type()
            self.assertTrue(first_result)

        # Second call with custom - should return different result
        with mock.patch(
            "guardian.conf.settings.GET_CONTENT_TYPE",
            "guardian.testapp.tests.test_managers.get_parent_content_type",
        ):
            second_result = _is_using_default_content_type()
            self.assertFalse(second_result)

        # Third call with default again - should work without caching issues
        with mock.patch("guardian.conf.settings.GET_CONTENT_TYPE", "guardian.ctypes.get_default_content_type"):
            third_result = _is_using_default_content_type()
            self.assertTrue(third_result)
