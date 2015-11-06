from __future__ import unicode_literals
from django.test import TestCase
from guardian.compat import mock
from guardian.managers import UserObjectPermissionManager
from guardian.managers import GroupObjectPermissionManager


class TestManagers(TestCase):

    def test_user_manager_assign(self):
        manager = UserObjectPermissionManager()
        manager.assign_perm = mock.Mock()
        manager.assign('perm', 'user', 'object')
        manager.assign_perm.assert_called_once_with('perm', 'user', 'object')

    def test_group_manager_assign(self):
        manager = GroupObjectPermissionManager()
        manager.assign_perm = mock.Mock()
        manager.assign('perm', 'group', 'object')
        manager.assign_perm.assert_called_once_with('perm', 'group', 'object')

