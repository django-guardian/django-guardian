from django.contrib.auth.models import User
from django.test import TestCase

from guardian.shortcuts import assign, remove_perm
from guardian.tests.app.models import KeyValue

class CustomPKModelTest(TestCase):
    """
    Tests agains custom model with primary key other than *standard*
    ``id`` integer field.
    """

    def setUp(self):
        self.user = User.objects.create(username='joe')
        self.keyval = KeyValue.objects.create(key='foo', value='bar')

    def test_assign(self):
        assign('guardian.change_keyvalue', self.user, self.keyval)
        self.assertTrue(self.user.has_perm('guardian.change_keyvalue',
            self.keyval))

    def test_remove_perm(self):
        assign('guardian.change_keyvalue', self.user, self.keyval)
        self.assertTrue(self.user.has_perm('guardian.change_keyvalue',
            self.keyval))
        remove_perm('guardian.change_keyvalue', self.user, self.keyval)
        self.assertFalse(self.user.has_perm('guardian.change_keyvalue',
            self.keyval))

