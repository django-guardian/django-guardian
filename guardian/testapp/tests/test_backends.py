from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase

from guardian.backends import ObjectPermissionBackend
from guardian.conf import settings as guardian_settings
from guardian.shortcuts import assign_perm, remove_perm
from guardian.testapp.models import Project

User = get_user_model()


class ObjectPermissionBackendTest(TestCase):
    def setUp(self):
        self.backend = ObjectPermissionBackend()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.superuser = User.objects.create_superuser(username="superuser", password="superpass")
        self.inactive_user = User.objects.create_user(username="inactive", password="inactive")
        self.inactive_user.is_active = False
        self.inactive_user.save()

        self.group = Group.objects.create(name="testgroup")
        self.user.groups.add(self.group)

        self.project = Project.objects.create(name="Test Project")

        # Create anonymous user if it doesn't exist
        try:
            self.anonymous_user = User.objects.get(username=guardian_settings.ANONYMOUS_USER_NAME)
        except User.DoesNotExist:
            self.anonymous_user = User.objects.create_user(username=guardian_settings.ANONYMOUS_USER_NAME)

    def test_authenticate_returns_none(self):
        """Backend should not authenticate users (returns None)"""
        result = self.backend.authenticate(request=None, username="test", password="test")
        self.assertIsNone(result)

    def test_has_perm_with_object(self):
        """Test has_perm method with object permissions"""
        # No permission initially
        self.assertFalse(self.backend.has_perm(self.user, "change_project", self.project))

        # Assign permission
        assign_perm("change_project", self.user, self.project)
        self.assertTrue(self.backend.has_perm(self.user, "change_project", self.project))

    def test_has_perm_without_object(self):
        """Test has_perm method without object (should return False)"""
        # ObjectPermissionBackend only handles object-level permissions
        self.assertFalse(self.backend.has_perm(self.user, "change_project"))

    def test_has_perm_superuser(self):
        """Test has_perm method with superuser"""
        self.assertTrue(self.backend.has_perm(self.superuser, "change_project", self.project))

    def test_has_perm_inactive_user(self):
        """Test has_perm method with inactive user"""
        assign_perm("change_project", self.inactive_user, self.project)
        self.assertFalse(self.backend.has_perm(self.inactive_user, "change_project", self.project))

    def test_get_group_permissions_with_object(self):
        """Test get_group_permissions method with object"""
        # No permissions initially
        perms = self.backend.get_group_permissions(self.user, self.project)
        self.assertEqual(set(), perms)

        # Assign permission to group
        assign_perm("change_project", self.group, self.project)
        perms = self.backend.get_group_permissions(self.user, self.project)
        self.assertIn("change_project", perms)

    def test_get_group_permissions_without_object(self):
        """Test get_group_permissions method without object (should return empty set)"""
        perms = self.backend.get_group_permissions(self.user)
        self.assertEqual(set(), perms)

    def test_get_group_permissions_inactive_user(self):
        """Test get_group_permissions method with inactive user"""
        assign_perm("change_project", self.group, self.project)
        perms = self.backend.get_group_permissions(self.inactive_user, self.project)
        self.assertEqual(set(), perms)

    def test_get_group_permissions_anonymous_user(self):
        """Test get_group_permissions method with anonymous user"""
        anonymous = AnonymousUser()
        perms = self.backend.get_group_permissions(anonymous, self.project)
        # Should return empty set for anonymous users (unless configured)
        self.assertEqual(set(), perms)

    def test_get_all_permissions_with_object(self):
        """Test get_all_permissions method with object"""
        # No permissions initially
        perms = self.backend.get_all_permissions(self.user, self.project)
        self.assertEqual(set(), perms)

        # Assign user permission
        assign_perm("change_project", self.user, self.project)
        perms = self.backend.get_all_permissions(self.user, self.project)
        self.assertIn("change_project", perms)

        # Assign group permission
        assign_perm("delete_project", self.group, self.project)
        perms = self.backend.get_all_permissions(self.user, self.project)
        self.assertIn("change_project", perms)
        self.assertIn("delete_project", perms)

    def test_get_all_permissions_without_object(self):
        """Test get_all_permissions method without object"""
        perms = self.backend.get_all_permissions(self.user)
        self.assertEqual(set(), perms)

    def test_get_all_permissions_superuser(self):
        """Test get_all_permissions method with superuser"""
        perms = self.backend.get_all_permissions(self.superuser, self.project)
        # Superuser should have all permissions for the content type
        self.assertGreater(len(list(perms)), 0)

    def test_mixed_user_and_group_permissions(self):
        """Test that both user and group permissions are returned correctly"""
        # Assign different permissions to user and group
        assign_perm("change_project", self.user, self.project)
        assign_perm("delete_project", self.group, self.project)

        # get_group_permissions should only return group permissions
        group_perms = self.backend.get_group_permissions(self.user, self.project)
        self.assertIn("delete_project", group_perms)
        self.assertNotIn("change_project", group_perms)

        # get_all_permissions should return both
        all_perms = self.backend.get_all_permissions(self.user, self.project)
        self.assertIn("change_project", all_perms)
        self.assertIn("delete_project", all_perms)

    def test_permission_removal(self):
        """Test that permission removal works correctly"""
        # Assign permissions
        assign_perm("change_project", self.user, self.project)
        assign_perm("delete_project", self.group, self.project)

        # Verify they exist
        self.assertTrue(self.backend.has_perm(self.user, "change_project", self.project))
        group_perms = self.backend.get_group_permissions(self.user, self.project)
        self.assertIn("delete_project", group_perms)

        # Remove permissions
        remove_perm("change_project", self.user, self.project)
        remove_perm("delete_project", self.group, self.project)

        # Verify they're gone
        self.assertFalse(self.backend.has_perm(self.user, "change_project", self.project))
        group_perms = self.backend.get_group_permissions(self.user, self.project)
        self.assertEqual(set(), group_perms)

    def test_user_in_multiple_groups(self):
        """Test permissions when user belongs to multiple groups"""
        group1 = Group.objects.create(name="group1")
        group2 = Group.objects.create(name="group2")

        self.user.groups.add(group1, group2)

        # Assign different permissions to different groups
        assign_perm("change_project", group1, self.project)
        assign_perm("delete_project", group2, self.project)

        # User should get permissions from both groups
        group_perms = self.backend.get_group_permissions(self.user, self.project)
        self.assertIn("change_project", group_perms)
        self.assertIn("delete_project", group_perms)

    def test_backend_attributes(self):
        """Test that backend has correct attributes"""
        self.assertTrue(self.backend.supports_object_permissions)
        self.assertTrue(self.backend.supports_anonymous_user)
        self.assertTrue(self.backend.supports_inactive_user)
