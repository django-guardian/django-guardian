from django.test import TestCase

from guardian.conf import settings
from guardian.compat import get_user_model
from guardian.management import create_anonymous_user


User = get_user_model()


class CustomUserTests(TestCase):
    def test_create_anonymous_user(self):
        create_anonymous_user(object())
        self.assertEqual(1, User.objects.all().count())
        anonymous = User.objects.all()[0]
        self.assertEqual(anonymous.pk, settings.ANONYMOUS_USER_ID)

