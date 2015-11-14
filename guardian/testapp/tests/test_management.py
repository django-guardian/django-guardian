from __future__ import absolute_import
from __future__ import unicode_literals

from guardian.compat import get_user_model
from guardian.compat import mock
from guardian.compat import unittest
from guardian.management import create_anonymous_user
from guardian.utils import get_anonymous_user


mocked_get_init_anon = mock.Mock()


class TestGetAnonymousUser(unittest.TestCase):

    @mock.patch('guardian.management.guardian_settings')
    def test_uses_custom_function(self, guardian_settings):
        mocked_get_init_anon.reset_mock()

        path = 'guardian.testapp.tests.test_management.mocked_get_init_anon'
        guardian_settings.GET_INIT_ANONYMOUS_USER = path
        guardian_settings.ANONYMOUS_USER_ID = 219
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()

        create_anonymous_user('sender')

        mocked_get_init_anon.assert_called_once_with(User)

        self.assertEqual(anon.pk, 219)
        anon.save.assert_called_once_with()

    def test_get_anonymous_user(self):
        anon = get_anonymous_user()
        self.assertFalse(anon.has_usable_password())
        self.assertEqual(anon.username, "AnonymousUser")
        self.assertEqual(anon.pk, -1)
