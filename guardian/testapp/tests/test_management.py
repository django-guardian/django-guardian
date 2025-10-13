from copy import deepcopy
from unittest import mock
import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import DatabaseError
from django.test import TestCase, override_settings

from guardian.management import create_anonymous_user
from guardian.utils import get_anonymous_user

mocked_get_init_anon = mock.Mock()
multi_db_dict = {
    "default": deepcopy(settings.DATABASES["default"]),
    "session": deepcopy(settings.DATABASES["default"]),
}


class SessionRouter:
    @staticmethod
    def db_for_write(model, **kwargs):
        if model == Session:
            return "session"
        else:
            return None

    @staticmethod
    def allow_migrate(db, app_label, **kwargs):
        if db == "session":
            return app_label == "sessions"
        else:
            return None


class TestGetAnonymousUser(TestCase):
    @mock.patch("guardian.management.guardian_settings")
    def test_uses_custom_function(self, guardian_settings):
        mocked_get_init_anon.reset_mock()

        path = "guardian.testapp.tests.test_management.mocked_get_init_anon"
        guardian_settings.GET_INIT_ANONYMOUS_USER = path
        guardian_settings.ANONYMOUS_USER_NAME = "anonymous"
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()

        create_anonymous_user("sender", using="default")

        mocked_get_init_anon.assert_called_once_with(User)

        anon.save.assert_called_once_with(using="default")

    @mock.patch("guardian.management.guardian_settings")
    @override_settings(AUTH_USER_MODEL="testapp.CustomUsernameUser")
    def test_uses_custom_username_field_model(self, guardian_settings):
        mocked_get_init_anon.reset_mock()
        guardian_settings.GET_INIT_ANONYMOUS_USER = "guardian.testapp.tests.test_management.mocked_get_init_anon"
        guardian_settings.ANONYMOUS_USER_NAME = "testuser@example.com"
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()
        create_anonymous_user("sender", using="default")
        mocked_get_init_anon.assert_called_once_with(User)
        anon.save.assert_called_once_with(using="default")

    def test_get_anonymous_user(self):
        anon = get_anonymous_user()
        self.assertFalse(anon.has_usable_password())
        self.assertEqual(anon.get_username(), "AnonymousUser")

    @mock.patch("guardian.management.guardian_settings")
    def test_non_migrated_db(self, guardian_settings):
        mocked_get_init_anon.reset_mock()
        guardian_settings.GET_INIT_ANONYMOUS_USER = "guardian.testapp.tests.test_management.mocked_get_init_anon"

        # Suppress the DATABASES override warning for this specific test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with override_settings(DATABASE_ROUTERS=[SessionRouter()], DATABASES=multi_db_dict):
                create_anonymous_user("sender", using="session")

        mocked_get_init_anon.assert_not_called()

    @mock.patch("guardian.management.guardian_settings")
    def test_database_error_on_user_lookup(self, guardian_settings):
        """Test that DatabaseError is handled gracefully when User table doesn't exist (issue #770)"""
        guardian_settings.GET_INIT_ANONYMOUS_USER = "guardian.management.get_init_anonymous_user"
        guardian_settings.ANONYMOUS_USER_NAME = "anonymous"

        User = get_user_model()

        # Mock User.objects.using().get() to raise DatabaseError (simulating missing table)
        with mock.patch.object(User.objects, "using") as mock_using:
            mock_manager = mock.Mock()
            mock_using.return_value = mock_manager
            mock_manager.get.side_effect = DatabaseError("relation 'auth_user' does not exist")

            # This should not raise an exception - it should handle DatabaseError gracefully
            try:
                create_anonymous_user("sender", using="default")
                # If we reach here, the function handled the DatabaseError correctly
                success = True
            except DatabaseError:
                success = False

        self.assertTrue(success, "create_anonymous_user should handle DatabaseError gracefully")

    @mock.patch("guardian.management.guardian_settings")
    def test_database_error_on_user_save(self, guardian_settings):
        """Test that DatabaseError is handled gracefully when saving fails due to missing table (issue #770)"""
        guardian_settings.GET_INIT_ANONYMOUS_USER = "guardian.management.get_init_anonymous_user"
        guardian_settings.ANONYMOUS_USER_NAME = "anonymous"

        User = get_user_model()

        # Mock User.objects.using().get() to raise DoesNotExist (user doesn't exist)
        # Then mock save() to raise DatabaseError (table doesn't exist)
        with mock.patch.object(User.objects, "using") as mock_using:
            mock_manager = mock.Mock()
            mock_using.return_value = mock_manager
            mock_manager.get.side_effect = User.DoesNotExist()

            # Mock user.save() to raise DatabaseError
            with mock.patch("guardian.management.get_init_anonymous_user") as mock_get_init:
                mock_user = mock.Mock()
                mock_user.save.side_effect = DatabaseError("relation 'auth_user' does not exist")
                mock_get_init.return_value = mock_user

                # This should not raise an exception
                try:
                    create_anonymous_user("sender", using="default")
                    success = True
                except DatabaseError:
                    success = False

        self.assertTrue(success, "create_anonymous_user should handle DatabaseError on save gracefully")
