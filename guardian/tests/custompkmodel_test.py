
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from guardian.shortcuts import assign, remove_perm
from guardian.models import User, Group, Permission, AnonymousUser

class CustomPKModelTest(TestCase):
    """
    Tests agains custom model with primary key other than *standard*
    ``id`` integer field.
    """

    def setUp(self):
        self.user = User.objects.create(username='joe')
        self.ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')

    def test_assign(self):
        assign('contenttypes.change_contenttype', self.user, self.ctype)
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
            self.ctype))

    def test_remove_perm(self):
        assign('contenttypes.change_contenttype', self.user, self.ctype)
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
            self.ctype))
        remove_perm('contenttypes.change_contenttype', self.user, self.ctype)
        self.assertFalse(self.user.has_perm('contenttypes.change_contenttype',
            self.ctype))

