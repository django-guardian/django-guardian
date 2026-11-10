"""
Integration tests to verify that the new backend methods work correctly
with Django's authentication system.
"""

from unittest import skipIf
from unittest.mock import patch

from asgiref.sync import async_to_sync, sync_to_async
import django
from django.contrib.auth import authenticate, get_permission_codename, get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase, override_settings

from guardian.conf import settings as guardian_settings
from guardian.shortcuts import assign_perm
from guardian.testapp.models import Project
from guardian.testapp.tests.test_backends import OBJECT_FACTORIES

User = get_user_model()

MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"
GUARDIAN_BACKEND = "guardian.backends.ObjectPermissionBackend"
BACKEND_ORDERS = (
    (GUARDIAN_BACKEND, MODEL_BACKEND),
    (MODEL_BACKEND, GUARDIAN_BACKEND),
)


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


@skipIf(django.VERSION < (5, 2), "Async backends are supported on Django 5.2 and above")
class UserApiTest(TestCase):
    """`user.has_perm()` and friends, and their async counterparts, which is what applications actually call.

    Each scenario checks the sync method and its async version against the same expected value.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.superuser = User.objects.create_superuser(username="superuser", password="superpass")
        self.inactive_user = User.objects.create_user(username="inactive", password="inactive", is_active=False)
        self.group = Group.objects.create(name="testgroup")
        self.user.groups.add(self.group)
        self.project = Project.objects.create(name="Test Project")
        self.anonymous_user = User.objects.get_or_create(username=guardian_settings.ANONYMOUS_USER_NAME)[0]

    # has_perm / ahas_perm

    def test_has_perm_with_direct_permission(self):
        assign_perm("change_project", self.user, self.project)
        self.assertTrue(self.user.has_perm("change_project", self.project))
        self.assertTrue(async_to_sync(self.user.ahas_perm)("change_project", self.project))
        self.assertFalse(self.user.has_perm("delete_project", self.project))
        self.assertFalse(async_to_sync(self.user.ahas_perm)("delete_project", self.project))

    def test_has_perm_with_group_permission(self):
        assign_perm("change_project", self.group, self.project)
        self.assertTrue(self.user.has_perm("change_project", self.project))
        self.assertTrue(async_to_sync(self.user.ahas_perm)("change_project", self.project))

    def test_has_perm_without_permission(self):
        self.assertFalse(self.user.has_perm("change_project", self.project))
        self.assertFalse(async_to_sync(self.user.ahas_perm)("change_project", self.project))

    def test_has_perm_with_full_permission_name(self):
        assign_perm("change_project", self.user, self.project)
        self.assertTrue(self.user.has_perm("testapp.change_project", self.project))
        self.assertTrue(async_to_sync(self.user.ahas_perm)("testapp.change_project", self.project))
        self.assertFalse(self.user.has_perm("testapp.delete_project", self.project))
        self.assertFalse(async_to_sync(self.user.ahas_perm)("testapp.delete_project", self.project))

    def test_has_perm_with_other_object_models(self):
        """Generic, mixed and non-integer primary key models, not only direct foreign keys."""
        for label, factory in OBJECT_FACTORIES:
            with self.subTest(model=label):
                obj = factory()
                change, delete = (
                    get_permission_codename("change", obj._meta),
                    get_permission_codename("delete", obj._meta),
                )
                assign_perm(change, self.user, obj)
                user = User.objects.get(pk=self.user.pk)  # a new instance has no prefetch cache
                self.assertTrue(user.has_perm(change, obj))
                self.assertTrue(async_to_sync(user.ahas_perm)(change, obj))
                self.assertFalse(user.has_perm(delete, obj))
                self.assertFalse(async_to_sync(user.ahas_perm)(delete, obj))

    # has_perms / ahas_perms

    def test_has_perms_when_all_are_granted(self):
        assign_perm("change_project", self.user, self.project)
        assign_perm("delete_project", self.user, self.project)
        perms = ["change_project", "delete_project"]
        self.assertTrue(self.user.has_perms(perms, self.project))
        self.assertTrue(async_to_sync(self.user.ahas_perms)(perms, self.project))

    def test_has_perms_when_only_some_are_granted(self):
        assign_perm("change_project", self.user, self.project)
        perms = ["change_project", "delete_project"]
        self.assertFalse(self.user.has_perms(perms, self.project))
        self.assertFalse(async_to_sync(self.user.ahas_perms)(perms, self.project))

    # get_user_permissions / aget_user_permissions

    def test_get_user_permissions_is_empty(self):
        """Not implemented by this backend, even for a direct permission: sync and async both return nothing."""
        assign_perm("change_project", self.user, self.project)
        self.assertEqual(set(), self.user.get_user_permissions(self.project))
        self.assertEqual(set(), async_to_sync(self.user.aget_user_permissions)(self.project))

    # get_group_permissions / aget_group_permissions

    def test_get_group_permissions(self):
        assign_perm("change_project", self.user, self.project)
        assign_perm("delete_project", self.group, self.project)
        self.assertEqual({"delete_project"}, self.user.get_group_permissions(self.project))
        self.assertEqual({"delete_project"}, async_to_sync(self.user.aget_group_permissions)(self.project))

    def test_get_group_permissions_without_permission(self):
        self.assertEqual(set(), self.user.get_group_permissions(self.project))
        self.assertEqual(set(), async_to_sync(self.user.aget_group_permissions)(self.project))

    # get_all_permissions / aget_all_permissions

    def test_get_all_permissions(self):
        assign_perm("change_project", self.user, self.project)
        assign_perm("delete_project", self.group, self.project)
        expected = {"change_project", "delete_project"}
        self.assertEqual(expected, self.user.get_all_permissions(self.project))
        self.assertEqual(expected, async_to_sync(self.user.aget_all_permissions)(self.project))

    def test_get_all_permissions_without_permission(self):
        self.assertEqual(set(), self.user.get_all_permissions(self.project))
        self.assertEqual(set(), async_to_sync(self.user.aget_all_permissions)(self.project))

    def test_get_all_permissions_with_other_object_models(self):
        for label, factory in OBJECT_FACTORIES:
            with self.subTest(model=label):
                obj = factory()
                change = get_permission_codename("change", obj._meta)
                assign_perm(change, self.user, obj)
                user = User.objects.get(pk=self.user.pk)  # a new instance has no prefetch cache
                expected = {change}
                self.assertEqual(expected, user.get_all_permissions(obj))
                self.assertEqual(expected, async_to_sync(user.aget_all_permissions)(obj))

    # inactive users

    def test_inactive_user_has_no_permissions(self):
        assign_perm("change_project", self.inactive_user, self.project)
        user = self.inactive_user
        self.assertFalse(user.has_perm("change_project", self.project))
        self.assertFalse(async_to_sync(user.ahas_perm)("change_project", self.project))
        self.assertFalse(user.has_perms(["change_project"], self.project))
        self.assertFalse(async_to_sync(user.ahas_perms)(["change_project"], self.project))
        self.assertEqual(set(), user.get_group_permissions(self.project))
        self.assertEqual(set(), async_to_sync(user.aget_group_permissions)(self.project))
        self.assertEqual(set(), user.get_all_permissions(self.project))
        self.assertEqual(set(), async_to_sync(user.aget_all_permissions)(self.project))

    def test_inactive_superuser_has_no_permissions(self):
        user = User.objects.create_superuser(username="inactive-super", password="x", is_active=False)
        self.assertFalse(user.has_perm("change_project", self.project))
        self.assertFalse(async_to_sync(user.ahas_perm)("change_project", self.project))
        self.assertEqual(set(), user.get_all_permissions(self.project))
        self.assertEqual(set(), async_to_sync(user.aget_all_permissions)(self.project))

    # superusers

    def test_active_superuser_has_every_permission(self):
        user = self.superuser
        every_perm = {"add_project", "change_project", "delete_project", "view_project"}
        self.assertTrue(user.has_perm("change_project", self.project))
        self.assertTrue(async_to_sync(user.ahas_perm)("change_project", self.project))
        self.assertEqual(every_perm, user.get_all_permissions(self.project))
        self.assertEqual(every_perm, async_to_sync(user.aget_all_permissions)(self.project))

    # anonymous users

    def test_anonymous_user_with_permissions(self):
        assign_perm("change_project", self.anonymous_user, self.project)
        anonymous = AnonymousUser()
        self.assertTrue(anonymous.has_perm("change_project", self.project))
        self.assertTrue(async_to_sync(anonymous.ahas_perm)("change_project", self.project))
        self.assertFalse(anonymous.has_perm("delete_project", self.project))
        self.assertFalse(async_to_sync(anonymous.ahas_perm)("delete_project", self.project))
        self.assertEqual({"change_project"}, anonymous.get_all_permissions(self.project))
        self.assertEqual({"change_project"}, async_to_sync(anonymous.aget_all_permissions)(self.project))

    def test_anonymous_user_without_permissions(self):
        anonymous = AnonymousUser()
        self.assertFalse(anonymous.has_perm("change_project", self.project))
        self.assertFalse(async_to_sync(anonymous.ahas_perm)("change_project", self.project))
        self.assertEqual(set(), anonymous.get_all_permissions(self.project))
        self.assertEqual(set(), async_to_sync(anonymous.aget_all_permissions)(self.project))

    def test_anonymous_user_disabled(self):
        """With ANONYMOUS_USER_NAME = None, anonymous users have nothing, even if the anonymous user has permissions."""
        assign_perm("change_project", self.anonymous_user, self.project)
        anonymous = AnonymousUser()
        with patch("guardian.conf.settings.ANONYMOUS_USER_NAME", None):
            self.assertFalse(anonymous.has_perm("change_project", self.project))
            self.assertFalse(async_to_sync(anonymous.ahas_perm)("change_project", self.project))
            self.assertEqual(set(), anonymous.get_all_permissions(self.project))
            self.assertEqual(set(), async_to_sync(anonymous.aget_all_permissions)(self.project))


class UserApiAutoPrefetchTest(UserApiTest):
    """The same tests, with `GUARDIAN_AUTO_PREFETCH` enabled."""

    def setUp(self):
        super().setUp()
        patcher = patch("guardian.conf.settings.AUTO_PREFETCH", True)
        patcher.start()
        self.addCleanup(patcher.stop)


class AuthenticateTest(TestCase):
    """`authenticate()`/`aauthenticate()` must work with the guardian backend configured, in any position."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_authenticate_wrong_password_returns_none(self):
        for backends in BACKEND_ORDERS:
            with self.subTest(backends=backends), override_settings(AUTHENTICATION_BACKENDS=backends):
                self.assertIsNone(authenticate(None, username="testuser", password="wrong"))

    def test_authenticate_valid_credentials(self):
        for backends in BACKEND_ORDERS:
            with self.subTest(backends=backends), override_settings(AUTHENTICATION_BACKENDS=backends):
                user = authenticate(None, username="testuser", password="testpass")
                self.assertEqual(self.user.pk, user.pk)
                self.assertEqual(MODEL_BACKEND, user.backend)

    @skipIf(django.VERSION < (5, 2), "Async backends are supported on Django 5.2 and above")
    async def test_aauthenticate_wrong_password_returns_none(self):
        from django.contrib.auth import aauthenticate  # Django 5.0+

        for backends in BACKEND_ORDERS:
            with self.subTest(backends=backends), override_settings(AUTHENTICATION_BACKENDS=backends):
                self.assertIsNone(await aauthenticate(None, username="testuser", password="wrong"))

    @skipIf(django.VERSION < (5, 2), "Async backends are supported on Django 5.2 and above")
    async def test_aauthenticate_valid_credentials(self):
        from django.contrib.auth import aauthenticate  # Django 5.0+

        for backends in BACKEND_ORDERS:
            with self.subTest(backends=backends), override_settings(AUTHENTICATION_BACKENDS=backends):
                user = await aauthenticate(None, username="testuser", password="testpass")
                self.assertEqual(self.user.pk, user.pk)
                self.assertEqual(MODEL_BACKEND, user.backend)


class ForceLoginTest(TestCase):
    """`force_login()`/`aforce_login()` must pick a backend able to load users, even if guardian's comes first."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_force_login_skips_backend(self):
        with override_settings(AUTHENTICATION_BACKENDS=(GUARDIAN_BACKEND, MODEL_BACKEND)):
            self.client.force_login(self.user)
            session_backend = self.client.session["_auth_user_backend"]
        self.assertEqual(MODEL_BACKEND, session_backend)

    @skipIf(django.VERSION < (5, 0), "aforce_login is available on Django 5.0 and above")
    async def test_aforce_login_skips_backend(self):
        with override_settings(AUTHENTICATION_BACKENDS=(GUARDIAN_BACKEND, MODEL_BACKEND)):
            await self.async_client.aforce_login(self.user)
            # `SessionStore.aget` only exists from Django 5.1
            session_backend = await sync_to_async(lambda: self.async_client.session["_auth_user_backend"])()
        self.assertEqual(MODEL_BACKEND, session_backend)
