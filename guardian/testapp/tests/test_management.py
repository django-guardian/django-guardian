from __future__ import absolute_import
from __future__ import unicode_literals
from django.test import TestCase, override_settings

from guardian.compat import get_user_model
import mock
from guardian.management import create_anonymous_user
from guardian.utils import get_anonymous_user


mocked_get_init_anon = mock.Mock()


class TestGetAnonymousUser(TestCase):

    @mock.patch('guardian.management.guardian_settings')
    def test_uses_custom_function(self, guardian_settings):
        mocked_get_init_anon.reset_mock()

        path = 'guardian.testapp.tests.test_management.mocked_get_init_anon'
        guardian_settings.GET_INIT_ANONYMOUS_USER = path
        guardian_settings.ANONYMOUS_USER_NAME = "anonymous"
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()

        create_anonymous_user('sender')

        mocked_get_init_anon.assert_called_once_with(User)

        anon.save.assert_called_once_with()

    @mock.patch('guardian.management.guardian_settings')
    @override_settings(AUTH_USER_MODEL='testapp.CustomUsernameUser')
    def test_uses_custom_username_field_model(self, guardian_settings):
        mocked_get_init_anon.reset_mock()
        guardian_settings.GET_INIT_ANONYMOUS_USER = 'guardian.testapp.tests.test_management.mocked_get_init_anon'
        guardian_settings.ANONYMOUS_USER_NAME = 'testuser@example.com'
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()
        create_anonymous_user('sender')
        mocked_get_init_anon.assert_called_once_with(User)
        anon.save.assert_called_once_with()

    def test_get_anonymous_user(self):
        anon = get_anonymous_user()
        self.assertFalse(anon.has_usable_password())
        self.assertEqual(anon.get_username(), "AnonymousUser")
