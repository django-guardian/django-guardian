
from django.test import TestCase
from guardian.checks import check_settings


class SystemCheckTestCase(TestCase):
    def test_checks(self):
        """ Test custom system checks
        :return: None
        """
        self.assertFalse(check_settings(None))

        with self.settings(
                AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',),
                ANONYMOUS_USER_ID=None,
                ):
            self.assertEqual(len(check_settings(None)), 2)
