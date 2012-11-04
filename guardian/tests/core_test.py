from itertools import chain

from django.conf import settings
from django.contrib.auth import models as auth_app
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from guardian.core import ObjectPermissionChecker
from guardian.exceptions import NotUserNorGroup
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.shortcuts import assign
from guardian.models import User, Group, Permission, AnonymousUser

class ObjectPermissionTestCase(TestCase):

    def setUp(self):
        self.group, created = Group.objects.get_or_create(name='jackGroup')
        self.user, created = User.objects.get_or_create(username='jack')
        self.user.groups.add(self.group)
        self.ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        self.anonymous_user, created = User.objects.get_or_create(
            id=settings.ANONYMOUS_USER_ID,
            username='AnonymousUser')


class ObjectPermissionCheckerTest(ObjectPermissionTestCase):

    def setUp(self):
        super(ObjectPermissionCheckerTest, self).setUp()
        # Required if MySQL backend is used :/
        create_permissions(auth_app, [], 1)

    def test_cache_for_queries_count(self):
        settings.DEBUG = True
        try:
            from django.db import connection

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
            user_or_group=ContentType())
        self.assertRaises(NotUserNorGroup, ObjectPermissionChecker)

    def test_anonymous_user(self):
        user = AnonymousUser()
        check = ObjectPermissionChecker(user)
        # assert anonymous user has no object permissions at all for obj
        self.assertTrue( [] == list(check.get_perms(self.ctype)) )

    def test_superuser(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        check = ObjectPermissionChecker(user)
        ctype = ContentType.objects.get_for_model(self.ctype)
        perms = sorted(chain(*Permission.objects
            .filter(content_type=ctype)
            .values_list('codename')))
        self.assertEqual(perms, check.get_perms(self.ctype))
        for perm in perms:
            self.assertTrue(check.has_perm(perm, self.ctype))

    def test_not_active_superuser(self):
        user = User.objects.create(username='not_active_superuser',
            is_superuser=True, is_active=False)
        check = ObjectPermissionChecker(user)
        ctype = ContentType.objects.get_for_model(self.ctype)
        perms = sorted(chain(*Permission.objects
            .filter(content_type=ctype)
            .values_list('codename')))
        self.assertEqual(check.get_perms(self.ctype), [])
        for perm in perms:
            self.assertFalse(check.has_perm(perm, self.ctype))

    def test_not_active_user(self):
        user = User.objects.create(username='notactive')
        assign("change_contenttype", user, self.ctype)

        # new ObjectPermissionChecker is created for each User.has_perm call
        self.assertTrue(user.has_perm("change_contenttype", self.ctype))
        user.is_active = False
        self.assertFalse(user.has_perm("change_contenttype", self.ctype))

        # use on one checker only (as user's is_active attr should be checked
        # before try to use cache
        user = User.objects.create(username='notactive-cache')
        assign("change_contenttype", user, self.ctype)

        check = ObjectPermissionChecker(user)
        self.assertTrue(check.has_perm("change_contenttype", self.ctype))
        user.is_active = False
        self.assertFalse(check.has_perm("change_contenttype", self.ctype))

    def test_get_perms(self):
        group = Group.objects.create(name='group')
        obj1 = ContentType.objects.create(name='ct1', model='foo',
            app_label='guardian-tests')
        obj2 = ContentType.objects.create(name='ct2', model='bar',
            app_label='guardian-tests')

        assign_perms = {
            group: ('change_group', 'delete_group'),
            obj1: ('change_contenttype', 'delete_contenttype'),
            obj2: ('delete_contenttype',),
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

