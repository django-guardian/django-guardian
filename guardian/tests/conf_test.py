import mock
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from guardian.conf import settings as guardian_settings


class TestConfiguration(TestCase):

    def test_check_configuration(self):
        
        with mock.patch('guardian.conf.settings.RENDER_403', True):
            with mock.patch('guardian.conf.settings.RAISE_403', True):
                self.assertRaises(ImproperlyConfigured,
                    guardian_settings.check_configuration)

