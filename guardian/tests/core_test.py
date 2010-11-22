from itertools import chain

from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.flatpages.models import FlatPage

from guardian.core import ObjectPermissionChecker
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.exceptions import NotUserNorGroup
from guardian.shortcuts import assign
from guardian.tests.app.models import Keycard

class ObjectPermissionTestCase(TestCase):
    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='jack')
        self.group = Group.objects.get(name='jackGroup')
        UserObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        self.flatpage = FlatPage.objects.create(title='Any page', url='/any/')

class ObjectPermissionCheckerTest(ObjectPermissionTestCase):

    def test_cache_for_queries_count(self):
        from django.conf import settings
        settings.DEBUG = True
        try:
            from django.db import connection
            UserObjectPermission.objects.all().delete()
            GroupObjectPermission.objects.all().delete()

            ContentType.objects.clear_cache()
            checker = ObjectPermissionChecker(self.user)

            # has_perm on Checker should spawn only one query plus one extra for
            # fetching the content type first time we check for specific model
            query_count = len(connection.queries)
            res = checker.has_perm("change_group", self.group)
            self.assertEqual(len(connection.queries), query_count + 2)

            # Checking again shouldn't spawn any queries
            query_count = len(connection.queries)
            res_new = checker.has_perm("change_group", self.group)
            self.assertEqual(res, res_new)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            query_count = len(connection.queries)
            checker.has_perm("delete_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance should spawn 1 query
            new_group = Group.objects.create(name='new-group')
            query_count = len(connection.queries)
            checker.has_perm("change_group", new_group)
            self.assertEqual(len(connection.queries), query_count + 1)

            # Checking for permission for other model should spawn 2 queries
            # (again: content type and actual permissions for the object)
            query_count = len(connection.queries)
            checker.has_perm("change_user", self.user)
            self.assertEqual(len(connection.queries), query_count + 2)

        finally:
            settings.DEBUG = False

    def test_init(self):
        self.assertRaises(NotUserNorGroup, ObjectPermissionChecker,
            user_or_group=Keycard())
        self.assertRaises(NotUserNorGroup, ObjectPermissionChecker)

    def test_anonymous_user(self):
        user = AnonymousUser()
        check = ObjectPermissionChecker(user)
        # assert anonymous user has no object permissions at all for flatpage
        self.assertTrue( [] == list(check.get_perms(self.flatpage)) )

    def test_superuser(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        check = ObjectPermissionChecker(user)
        ctype = ContentType.objects.get_for_model(self.flatpage)
        perms = sorted(chain(*Permission.objects
            .filter(content_type=ctype)
            .values_list('codename')))
        self.assertEqual(perms, check.get_perms(self.flatpage))
        for perm in perms:
            self.assertTrue(check.has_perm(perm, self.flatpage))

    def test_not_active_superuser(self):
        user = User.objects.create(username='not_active_superuser',
            is_superuser=True, is_active=False)
        check = ObjectPermissionChecker(user)
        ctype = ContentType.objects.get_for_model(self.flatpage)
        perms = sorted(chain(*Permission.objects
            .filter(content_type=ctype)
            .values_list('codename')))
        self.assertEqual(check.get_perms(self.flatpage), [])
        for perm in perms:
            self.assertFalse(check.has_perm(perm, self.flatpage))

    def test_not_active_user(self):
        user = User.objects.create(username='notactive')
        assign("change_flatpage", user, self.flatpage)

        # new ObjectPermissionChecker is created for each User.has_perm call
        self.assertTrue(user.has_perm("change_flatpage", self.flatpage))
        user.is_active = False
        self.assertFalse(user.has_perm("change_flatpage", self.flatpage))

        # use on one checker only (as user's is_active attr should be checked
        # before try to use cache
        user = User.objects.create(username='notactive-cache')
        assign("change_flatpage", user, self.flatpage)

        check = ObjectPermissionChecker(user)
        self.assertTrue(check.has_perm("change_flatpage", self.flatpage))
        user.is_active = False
        self.assertFalse(check.has_perm("change_flatpage", self.flatpage))

    def test_get_perms(self):
        group = Group.objects.create(name='group')
        key1 = Keycard.objects.create(key='key1')
        key2 = Keycard.objects.create(key='key2')

        assign_perms = {
            group: ('change_group', 'delete_group'),
            key1: ('change_keycard', 'can_use_keycard', 'can_suspend_keycard'),
            key2: ('delete_keycard', 'can_suspend_keycard'),
        }

        check = ObjectPermissionChecker(self.user)

        for obj, perms in assign_perms.items():
            for perm in perms:
                UserObjectPermission.objects.assign(perm, self.user, obj)
            self.assertEqual(sorted(perms), sorted(check.get_perms(obj)))

        check = ObjectPermissionChecker(self.group)

        for obj, perms in assign_perms.items():
            for perm in perms:
                GroupObjectPermission.objects.assign(perm, self.group, obj)
            self.assertEqual(sorted(perms), sorted(check.get_perms(obj)))

