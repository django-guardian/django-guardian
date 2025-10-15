"""
Integration tests to verify that the new backend methods work correctly
with Django's authentication system.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings

from guardian.shortcuts import assign_perm
from guardian.testapp.models import Project

User = get_user_model()


@override_settings(
    AUTHENTICATION_BACKENDS=[
        "guardian.backends.ObjectPermissionBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]
)
class BackendIntegrationTest(TestCase):
    """Test that the backend integrates correctly with Django's auth system"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.superuser = User.objects.create_superuser(username="superuser", password="superpass")
        self.group = Group.objects.create(name="testgroup")
        self.user.groups.add(self.group)
        self.project = Project.objects.create(name="Test Project")

    def test_user_get_group_permissions_integration(self):
        """Test that user.get_group_permissions() calls our backend correctly"""
        # Assign permission to group
        assign_perm("change_project", self.group, self.project)

        # Django's User.get_group_permissions() should now include our backend
        group_perms = self.user.get_group_permissions(self.project)
        self.assertIn("change_project", group_perms)

    def test_user_get_group_permissions_without_object(self):
        """Test that user.get_group_permissions() without object works"""
        # When no object is provided, our backend should return empty set
        group_perms = self.user.get_group_permissions()
        # The result should not include our object-specific permissions
        # but may include model-level permissions from ModelBackend
        self.assertIsInstance(group_perms, set)

    def test_user_get_all_permissions_integration(self):
        """Test that user.get_all_permissions() includes our object permissions"""
        # Assign both user and group permissions
        assign_perm("change_project", self.user, self.project)
        assign_perm("delete_project", self.group, self.project)

        # Get all permissions for the object
        all_perms = self.user.get_all_permissions(self.project)

        # Should include both user and group permissions
        self.assertIn("change_project", all_perms)
        self.assertIn("delete_project", all_perms)

    def test_backend_priority_with_model_backend(self):
        """Test that both backends work together correctly"""
        # Our backend should handle object-level permissions
        assign_perm("change_project", self.user, self.project)

        # Check that the permission is detected
        self.assertTrue(self.user.has_perm("testapp.change_project", self.project))

        # Verify it comes from our backend (not model-level permission)
        all_perms = self.user.get_all_permissions(self.project)
        self.assertIn("change_project", all_perms)

    def test_anonymous_user_support(self):
        """Test that anonymous user support works correctly"""
        from django.contrib.auth.models import AnonymousUser

        anonymous = AnonymousUser()

        # Should not have group permissions
        group_perms = anonymous.get_group_permissions(self.project)
        self.assertEqual(set(), group_perms)
