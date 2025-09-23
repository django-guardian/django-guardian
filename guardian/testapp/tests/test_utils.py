from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase, override_settings

from guardian.exceptions import NotUserNorGroup
from guardian.models import GroupObjectPermission, UserObjectPermission, UserObjectPermissionBase
from guardian.testapp.models import Project, ProjectGroupObjectPermission, ProjectUserObjectPermission
from guardian.testapp.tests.conf import skipUnlessTestApp
from guardian.testapp.tests.test_core import ObjectPermissionTestCase
from guardian.utils import (
    _get_anonymous_user_cached,
    _get_anonymous_user_uncached,
    get_anonymous_user,
    get_group_obj_perms_model,
    get_identity,
    get_obj_perms_model,
    get_user_obj_perms_model,
)

User = get_user_model()


class GetAnonymousUserTest(TestCase):
    def test(self):
        anon = get_anonymous_user()
        self.assertTrue(isinstance(anon, User))


class GetIdentityTest(ObjectPermissionTestCase):
    def test_user(self):
        user, group = get_identity(self.user)
        self.assertTrue(isinstance(user, User))
        self.assertEqual(group, None)

    def test_anonymous_user(self):
        anon = AnonymousUser()
        user, group = get_identity(anon)
        self.assertTrue(isinstance(user, User))
        self.assertEqual(group, None)

    def test_group(self):
        user, group = get_identity(self.group)
        self.assertTrue(isinstance(group, Group))
        self.assertEqual(user, None)

    def test_not_user_nor_group(self):
        self.assertRaises(NotUserNorGroup, get_identity, 1)
        self.assertRaises(NotUserNorGroup, get_identity, "User")
        self.assertRaises(NotUserNorGroup, get_identity, User)

    def test_multiple_user_qs(self):
        user, group = get_identity(User.objects.all())
        self.assertIsInstance(user, models.QuerySet)
        self.assertIsNone(group)

    def test_multiple_user_list(self):
        user, group = get_identity([self.user])
        self.assertIsInstance(user, list)
        self.assertIsNone(group)

    def test_multiple_group_qs(self):
        user, group = get_identity(Group.objects.all())
        self.assertIsInstance(group, models.QuerySet)
        self.assertIsNone(user)

    def test_multiple_group_list(self):
        user, group = get_identity([self.group])
        self.assertIsInstance(group, list)
        self.assertIsNone(user)

    def test_group_subclass_queryset(self):
        """Test that Group subclasses work with QuerySet identity resolution."""

        # Create a Group subclass to test the issubclass fix
        class TestTeam(Group):
            class Meta:
                proxy = True

        # Create a TestTeam instance
        team = TestTeam.objects.create(name="Test Team Subclass")

        # Test with QuerySet of Group subclass
        team_qs = TestTeam.objects.filter(pk=team.pk)
        user, group = get_identity(team_qs)
        self.assertIsInstance(group, models.QuerySet)
        self.assertIsNone(user)
        self.assertEqual(group.model, TestTeam)

        # Test with all TestTeams QuerySet
        all_teams_qs = TestTeam.objects.all()
        user, group = get_identity(all_teams_qs)
        self.assertIsInstance(group, models.QuerySet)
        self.assertIsNone(user)
        self.assertEqual(group.model, TestTeam)

        # Clean up
        team.delete()

    def test_user_subclass_queryset(self):
        """Test that User subclasses work with QuerySet identity resolution."""

        # Create a User subclass to test the issubclass fix
        class TestCustomUser(User):
            class Meta:
                proxy = True

        # Create a TestCustomUser instance
        custom_user = TestCustomUser.objects.create(username="testcustomuser_subclass")

        # Test with QuerySet of User subclass
        custom_user_qs = TestCustomUser.objects.filter(pk=custom_user.pk)
        user, group = get_identity(custom_user_qs)
        self.assertIsInstance(user, models.QuerySet)
        self.assertIsNone(group)
        self.assertEqual(user.model, TestCustomUser)

        # Test with all TestCustomUsers QuerySet
        all_custom_users_qs = TestCustomUser.objects.all()
        user, group = get_identity(all_custom_users_qs)
        self.assertIsInstance(user, models.QuerySet)
        self.assertIsNone(group)
        self.assertEqual(user.model, TestCustomUser)

        # Clean up
        custom_user.delete()


@skipUnlessTestApp
class GetUserObjPermsModelTest(TestCase):
    def test_for_instance(self):
        project = Project(name="Foobar")
        self.assertEqual(get_user_obj_perms_model(project), ProjectUserObjectPermission)

    def test_for_class(self):
        self.assertEqual(get_user_obj_perms_model(Project), ProjectUserObjectPermission)

    def test_default(self):
        self.assertEqual(get_user_obj_perms_model(ContentType), UserObjectPermission)

    def test_user_model(self):
        # this test assumes that there were no direct obj perms model to User
        # model defined (i.e. while testing guardian app in some custom
        # project)
        self.assertEqual(get_user_obj_perms_model(User), UserObjectPermission)


@skipUnlessTestApp
class GetGroupObjPermsModelTest(TestCase):
    def test_for_instance(self):
        project = Project(name="Foobar")
        self.assertEqual(get_group_obj_perms_model(project), ProjectGroupObjectPermission)

    def test_for_class(self):
        self.assertEqual(get_group_obj_perms_model(Project), ProjectGroupObjectPermission)

    def test_default(self):
        self.assertEqual(get_group_obj_perms_model(ContentType), GroupObjectPermission)

    def test_group_model(self):
        # this test assumes that there were no direct obj perms model to Group
        # model defined (i.e. while testing guardian app in some custom
        # project)
        self.assertEqual(get_group_obj_perms_model(Group), GroupObjectPermission)


class GetObjPermsModelTest(TestCase):
    def test_image_field(self):
        class SomeModel(models.Model):
            image = models.FileField(upload_to="images/")

        obj = SomeModel()
        perm_model = get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)
        self.assertEqual(perm_model, UserObjectPermission)

    def test_file_field(self):
        class SomeModel2(models.Model):
            file = models.FileField(upload_to="images/")

        obj = SomeModel2()
        perm_model = get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)
        self.assertEqual(perm_model, UserObjectPermission)


class GetAnonymousUserCacheTest(TestCase):
    """Test cases for get_anonymous_user caching functionality."""

    def setUp(self):
        # Clear any existing cache before each test
        if hasattr(_get_anonymous_user_cached, "cache_clear"):
            _get_anonymous_user_cached.cache_clear()

    def tearDown(self):
        # Clear cache after each test
        if hasattr(_get_anonymous_user_cached, "cache_clear"):
            _get_anonymous_user_cached.cache_clear()

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=0)
    def test_cache_disabled_by_default(self):
        """Test that caching is disabled by default."""
        with (
            patch("guardian.utils._get_anonymous_user_uncached") as mock_uncached,
            patch("guardian.utils._get_anonymous_user_cached") as mock_cached,
        ):
            mock_user = MagicMock()
            mock_uncached.return_value = mock_user

            # Call function multiple times
            result1 = get_anonymous_user()
            result2 = get_anonymous_user()

            # Should call uncached version each time
            self.assertEqual(mock_uncached.call_count, 2)
            self.assertEqual(mock_cached.call_count, 0)
            self.assertEqual(result1, mock_user)
            self.assertEqual(result2, mock_user)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=300)
    def test_cache_enabled(self):
        """Test that caching works when enabled."""
        # Reload the settings module to pick up the override
        from importlib import reload

        from guardian.conf import settings as guardian_settings_module

        reload(guardian_settings_module)

        with (
            patch("guardian.utils._get_anonymous_user_cached") as mock_cached,
            patch("guardian.utils._get_anonymous_user_uncached") as mock_uncached,
        ):
            mock_user = MagicMock()
            mock_cached.return_value = mock_user

            # Call function multiple times
            result1 = get_anonymous_user()
            result2 = get_anonymous_user()
            result3 = get_anonymous_user()

            # Should call cached version each time
            self.assertEqual(mock_cached.call_count, 3)
            self.assertEqual(mock_uncached.call_count, 0)
            self.assertEqual(result1, mock_user)
            self.assertEqual(result2, mock_user)
            self.assertEqual(result3, mock_user)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=0)
    def test_uncached_function_calls_database_each_time(self):
        """Test that uncached version calls database each time."""
        with (
            patch("guardian.utils.get_user_model") as mock_get_user_model,
            patch("guardian.conf.settings.ANONYMOUS_USER_NAME", "TestAnonymousUser"),
        ):
            mock_user_model = MagicMock()
            mock_user_model.USERNAME_FIELD = "username"
            mock_user_instance = MagicMock()
            mock_user_model.objects.get.return_value = mock_user_instance
            mock_get_user_model.return_value = mock_user_model

            # Call uncached function multiple times
            result1 = _get_anonymous_user_uncached()
            result2 = _get_anonymous_user_uncached()

            # Should call database each time
            self.assertEqual(mock_user_model.objects.get.call_count, 2)
            self.assertEqual(result1, mock_user_instance)
            self.assertEqual(result2, mock_user_instance)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=300)
    def test_cached_function_calls_database_once(self):
        """Test that cached version calls database only once."""
        with (
            patch("guardian.utils.get_user_model") as mock_get_user_model,
            patch("guardian.conf.settings.ANONYMOUS_USER_NAME", "TestAnonymousUser"),
            patch("guardian.utils.cache") as mock_cache,
        ):
            mock_user_model = MagicMock()
            mock_user_model.USERNAME_FIELD = "username"
            mock_user_instance = MagicMock()
            mock_user_model.objects.get.return_value = mock_user_instance
            mock_get_user_model.return_value = mock_user_model

            # Mock cache behavior - first call returns None (cache miss), subsequent calls return cached value
            call_count = 0

            def cache_get_side_effect(key):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return None  # Cache miss on first call
                return mock_user_instance  # Cache hit on subsequent calls

            mock_cache.get.side_effect = cache_get_side_effect
            mock_cache.set.return_value = None

            # Call cached function multiple times
            result1 = _get_anonymous_user_cached()
            result2 = _get_anonymous_user_cached()
            result3 = _get_anonymous_user_cached()

            # Should call database only once due to caching
            self.assertEqual(mock_user_model.objects.get.call_count, 1)
            self.assertEqual(result1, mock_user_instance)
            self.assertEqual(result2, mock_user_instance)
            self.assertEqual(result3, mock_user_instance)

            # Cache should be called for get operations
            self.assertEqual(mock_cache.get.call_count, 3)
            # Cache should be set once (on first call)
            self.assertEqual(mock_cache.set.call_count, 1)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=300)
    def test_cache_info_available(self):
        """Test that Django cache is working correctly."""
        with (
            patch("guardian.utils.get_user_model") as mock_get_user_model,
            patch("guardian.conf.settings.ANONYMOUS_USER_NAME", "TestAnonymousUser"),
            patch("guardian.utils.cache") as mock_cache,
        ):
            mock_user_model = MagicMock()
            mock_user_model.USERNAME_FIELD = "username"
            mock_user_instance = MagicMock()
            mock_user_model.objects.get.return_value = mock_user_instance
            mock_get_user_model.return_value = mock_user_model

            # Mock cache behavior
            mock_cache.get.side_effect = [None, mock_user_instance]  # First miss, then hit
            mock_cache.set.return_value = None

            # First call should hit database
            result1 = _get_anonymous_user_cached()
            self.assertEqual(mock_user_model.objects.get.call_count, 1)

            # Second call should use cache
            result2 = _get_anonymous_user_cached()
            self.assertEqual(mock_user_model.objects.get.call_count, 1)  # Still 1, no additional DB calls

            self.assertEqual(result1, result2)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=300)
    def test_cache_clear_functionality(self):
        """Test that cache can be cleared."""
        with (
            patch("guardian.utils.get_user_model") as mock_get_user_model,
            patch("guardian.conf.settings.ANONYMOUS_USER_NAME", "TestAnonymousUser"),
            patch("guardian.utils.cache") as mock_cache,
        ):
            mock_user_model = MagicMock()
            mock_user_model.USERNAME_FIELD = "username"
            mock_user_instance = MagicMock()
            mock_user_model.objects.get.return_value = mock_user_instance
            mock_get_user_model.return_value = mock_user_model

            # Mock cache behavior - simulate cache miss, hit, then miss again after clear
            mock_cache.get.side_effect = [None, mock_user_instance, None]
            mock_cache.set.return_value = None
            mock_cache.clear.return_value = None

            # Call function (cache miss - should hit DB)
            _get_anonymous_user_cached()
            self.assertEqual(mock_user_model.objects.get.call_count, 1)

            # Call again (cache hit - should not hit DB)
            _get_anonymous_user_cached()
            self.assertEqual(mock_user_model.objects.get.call_count, 1)

            # Clear cache and call again (cache miss - should hit DB again)
            mock_cache.clear()
            _get_anonymous_user_cached()
            self.assertEqual(mock_user_model.objects.get.call_count, 2)

    def test_both_functions_return_same_user(self):
        """Test that cached and uncached functions return the same user."""
        # Clear cache first
        if hasattr(_get_anonymous_user_cached, "cache_clear"):
            _get_anonymous_user_cached.cache_clear()

        cached_result = _get_anonymous_user_cached()
        uncached_result = _get_anonymous_user_uncached()

        # Both should return the same user
        self.assertEqual(cached_result.pk, uncached_result.pk)
        self.assertEqual(str(cached_result), str(uncached_result))
        self.assertTrue(isinstance(cached_result, User))
        self.assertTrue(isinstance(uncached_result, User))

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=300)
    def test_integration_with_get_identity(self):
        """Test that cached anonymous user works with get_identity function."""
        anon = AnonymousUser()

        # This test should use the actual implementation to ensure integration works
        user, group = get_identity(anon)

        # Should return a real user instance and None for group
        self.assertTrue(isinstance(user, User))
        self.assertIsNone(group)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=0)
    def test_integration_with_get_identity_uncached(self):
        """Test that uncached anonymous user works with get_identity function."""
        anon = AnonymousUser()

        # This test should use the actual implementation to ensure integration works
        user, group = get_identity(anon)

        # Should return a real user instance and None for group
        self.assertTrue(isinstance(user, User))
        self.assertIsNone(group)

    @override_settings(GUARDIAN_ANONYMOUS_USER_CACHE_TTL=-1)
    def test_indefinite_cache(self):
        """Test that TTL=-1 enables indefinite caching."""
        with patch("guardian.utils.guardian_settings") as mock_settings:
            mock_settings.ANONYMOUS_USER_CACHE_TTL = -1
            with (
                patch("guardian.utils._get_anonymous_user_cached") as mock_cached,
                patch("guardian.utils._get_anonymous_user_uncached") as mock_uncached,
            ):
                mock_user = MagicMock()
                mock_cached.return_value = mock_user

                # Call function - should use cached version
                result = get_anonymous_user()

                mock_cached.assert_called_once()
                mock_uncached.assert_not_called()
                self.assertEqual(result, mock_user)
