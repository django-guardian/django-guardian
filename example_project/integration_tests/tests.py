from django import VERSION
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.unittest import skipUnless

from guardian.compat import get_user_model
from guardian.management import create_anonymous_user


User = get_user_model()


@skipUnless(VERSION[:3] >= (1, 5, 0), 'Previous Django version do not support \
        custom models')
class CustomUserTests(TestCase):
    def test_create_anonymous_user(self):
        create_anonymous_user(object())
        self.assertEqual(1, User.objects.all().count())
