from unittest.mock import patch

from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase

from guardian.checks import check_active_users_only, check_settings


class SystemCheckTestCase(TestCase):
    def test_checks(self):
        """Test custom system checks
        :return: None
        """
        self.assertFalse(check_settings(None))

        with self.settings(
            AUTHENTICATION_BACKENDS=("django.contrib.auth.backends.ModelBackend",),
        ):
            self.assertEqual(len(check_settings(None)), 1)


class ActiveUsersOnlyCheckTestCase(TestCase):
    def test_no_warning_when_setting_disabled(self):
        with self.settings(GUARDIAN_ACTIVE_USERS_ONLY=False):
            result = check_active_users_only(None)
            self.assertEqual(result, [])

    def test_no_warning_when_user_model_has_is_active(self):
        with self.settings(GUARDIAN_ACTIVE_USERS_ONLY=True):
            result = check_active_users_only(None)
            self.assertEqual(result, [])

    def test_warning_when_user_model_lacks_is_active(self):
        def fake_get_field(name):
            if name == "is_active":
                raise FieldDoesNotExist()
            return original_get_field(name)

        from django.contrib.auth import get_user_model

        original_get_field = get_user_model()._meta.get_field

        with self.settings(GUARDIAN_ACTIVE_USERS_ONLY=True):
            with patch.object(type(get_user_model()._meta), "get_field", side_effect=fake_get_field):
                result = check_active_users_only(None)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, "guardian.W002")
