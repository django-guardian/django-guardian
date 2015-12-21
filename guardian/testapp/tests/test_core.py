from __future__ import unicode_literals
from itertools import chain

from django.conf import settings
# Try the new app settings (Django 1.7) and fall back to the old system
try:
    from django.apps import apps as django_apps
    auth_app = django_apps.get_app_config("auth")
except ImportError:
    from django.contrib.auth import models as auth_app
from django.contrib.auth.models import Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from guardian.core import ObjectPermissionChecker
from guardian.compat import get_user_model, create_permissions
from guardian.exceptions import NotUserNorGroup
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.shortcuts import assign_perm
from guardian.management import create_anonymous_user

User = get_user_model()


class CustomUserTests(TestCase):
    def test_create_anonymous_user(self):
        create_anonymous_user(object())
        self.assertEqual(1, User.objects.all().count())
        anonymous = User.objects.all()[0]
        self.assertEqual(anonymous.pk, settings.ANONYMOUS_USER_ID)


class ObjectPermissionTestCase(TestCase):

    def setUp(self):
        self.group, created = Group.objects.get_or_create(name='jackGroup')
        self.user, created = User.objects.get_or_create(username='jack')
        self.user.groups.add(self.group)
        self.ctype = ContentType.objects.create(model='bar', app_label='fake-for-guardian-tests')
        try:
            self.anonymous_user = User.objects.get(pk=settings.ANONYMOUS_USER_ID)
        except User.DoesNotExist:
            self.anonymous_user = User(
                id=settings.ANONYMOUS_USER_ID,
                username='AnonymousUser',
            )
            self.anonymous_user.save()


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

            # has_perm on Checker should spawn only two queries plus one extra
            # for fetching the content type first time we check for specific
            # model and two more content types as there are additional checks
            # at get_user_obj_perms_model and get_group_obj_perms_model
            query_count = len(connection.queries)
            res = checker.has_perm("change_group", self.group)
            if 'guardian.testapp' in settings.INSTALLED_APPS:
                expected = 5
            else:
                # TODO: This is strange, need to investigate; totally not sure
                # why there are more queries if testapp is not included
                expected = 11
            self.assertEqual(len(connection.queries), query_count + expected)

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

            # Checking for same model but other instance should spawn 2 queries
            new_group = Group.objects.create(name='new-group')
            query_count = len(connection.queries)
            checker.has_perm("change_group", new_group)
            self.assertEqual(len(connection.queries), query_count + 2)

            # Checking for permission for other model should spawn 3 queries
            # (again: content type and actual permissions for the object...
            query_count = len(connection.queries)
            checker.has_perm("change_user", self.user)
            self.assertEqual(len(connection.queries), query_count + 3)

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
        assign_perm("change_contenttype", user, self.ctype)

        # new ObjectPermissionChecker is created for each User.has_perm call
        self.assertTrue(user.has_perm("change_contenttype", self.ctype))
        user.is_active = False
        self.assertFalse(user.has_perm("change_contenttype", self.ctype))

        # use on one checker only (as user's is_active attr should be checked
        # before try to use cache
        user = User.objects.create(username='notactive-cache')
        assign_perm("change_contenttype", user, self.ctype)

        check = ObjectPermissionChecker(user)
        self.assertTrue(check.has_perm("change_contenttype", self.ctype))
        user.is_active = False
        self.assertFalse(check.has_perm("change_contenttype", self.ctype))

    def test_get_perms(self):
        group = Group.objects.create(name='group')
        obj1 = ContentType.objects.create(model='foo', app_label='guardian-tests')
        obj2 = ContentType.objects.create(model='bar', app_label='guardian-tests')

        assign_perms = {
            group: ('change_group', 'delete_group'),
            obj1: ('change_contenttype', 'delete_contenttype'),
            obj2: ('delete_contenttype',),
        }

        check = ObjectPermissionChecker(self.user)

        for obj, perms in assign_perms.items():
            for perm in perms:
                UserObjectPermission.objects.assign_perm(perm, self.user, obj)
            self.assertEqual(sorted(perms), sorted(check.get_perms(obj)))

        check = ObjectPermissionChecker(self.group)

        for obj, perms in assign_perms.items():
            for perm in perms:
                GroupObjectPermission.objects.assign_perm(perm, self.group, obj)
            self.assertEqual(sorted(perms), sorted(check.get_perms(obj)))

