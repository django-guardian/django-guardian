from unittest import mock
import warnings

from django.test import TestCase

from guardian.managers import GroupObjectPermissionManager, UserObjectPermissionManager


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
