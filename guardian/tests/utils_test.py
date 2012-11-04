
from django.test import TestCase

from guardian.tests.core_test import ObjectPermissionTestCase
from guardian.utils import get_anonymous_user, get_identity
from guardian.exceptions import NotUserNorGroup
from guardian.models import User, Group, AnonymousUser

class GetAnonymousUserTest(TestCase):

    def test(self):
        anon = get_anonymous_user()
        self.assertTrue(isinstance(anon, User))

class GetIdentityTest(ObjectPermissionTestCase):

    def test_user(self):
        user, group = get_identity(self.user)
        self.assertTrue(isinstance(user, User))
        self.assertEqual(group, None)

    def test_anonymous_user(self):
        anon = AnonymousUser()
        user, group = get_identity(anon)
        self.assertTrue(isinstance(user, User))
        self.assertEqual(group, None)

    def test_group(self):
        user, group = get_identity(self.group)
        self.assertTrue(isinstance(group, Group))
        self.assertEqual(user, None)

    def test_not_user_nor_group(self):
        self.assertRaises(NotUserNorGroup, get_identity, 1)
        self.assertRaises(NotUserNorGroup, get_identity, "User")
        self.assertRaises(NotUserNorGroup, get_identity, User)

