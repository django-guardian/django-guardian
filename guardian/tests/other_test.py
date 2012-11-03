
from itertools import chain
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

import guardian
from guardian.backends import ObjectPermissionBackend
from guardian.exceptions import GuardianError
from guardian.exceptions import NotUserNorGroup
from guardian.exceptions import ObjectNotPersisted
from guardian.exceptions import WrongAppError
from guardian.models import GroupObjectPermission
from guardian.models import UserObjectPermission
from guardian.models import AnonymousUser
from guardian.models import Group
from guardian.models import Permission
from guardian.models import User


class UserPermissionTests(TestCase):
    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='jack')
        self.ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        self.obj1 = ContentType.objects.create(name='ct1', model='foo',
            app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(name='ct2', model='bar',
            app_label='guardian-tests')

    def test_assignement(self):
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))

        UserObjectPermission.objects.assign('change_contenttype', self.user,
            self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
            self.ctype))

    def test_assignement_and_remove(self):
        UserObjectPermission.objects.assign('change_contenttype', self.user,
            self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))

        UserObjectPermission.objects.remove_perm('change_contenttype',
            self.user, self.ctype)
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))

    def test_ctypes(self):
        UserObjectPermission.objects.assign('change_contenttype', self.user, self.obj1)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))

        UserObjectPermission.objects.remove_perm('change_contenttype', self.user, self.obj1)
        UserObjectPermission.objects.assign('change_contenttype', self.user, self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

        UserObjectPermission.objects.assign('change_contenttype', self.user, self.obj1)
        UserObjectPermission.objects.assign('change_contenttype', self.user, self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))

        UserObjectPermission.objects.remove_perm('change_contenttype', self.user, self.obj1)
        UserObjectPermission.objects.remove_perm('change_contenttype', self.user, self.obj2)
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

    def test_get_for_object(self):
        perms = UserObjectPermission.objects.get_for_object(self.user, self.ctype)
        self.assertEqual(perms.count(), 0)

        to_assign = sorted([
            'delete_contenttype',
            'change_contenttype',
        ])

        for perm in to_assign:
            UserObjectPermission.objects.assign(perm, self.user, self.ctype)

        perms = UserObjectPermission.objects.get_for_object(self.user, self.ctype)
        codenames = sorted(chain(*perms.values_list('permission__codename')))

        self.assertEqual(to_assign, codenames)

    def test_assign_validation(self):
        self.assertRaises(Permission.DoesNotExist,
            UserObjectPermission.objects.assign, 'change_group', self.user,
            self.user)

        group = Group.objects.create(name='test_group_assign_validation')
        ctype = ContentType.objects.get_for_model(group)
        perm = Permission.objects.get(codename='change_user')

        create_info = dict(
            permission = perm,
            user = self.user,
            content_type = ctype,
            object_pk = group.pk
        )
        self.assertRaises(ValidationError, UserObjectPermission.objects.create,
            **create_info)

    def test_unicode(self):
        obj_perm = UserObjectPermission.objects.assign("change_user",
            self.user, self.user)
        self.assertTrue(isinstance(obj_perm.__unicode__(), unicode))

    def test_errors(self):
        not_saved_user = User(username='not_saved_user')
        self.assertRaises(ObjectNotPersisted,
            UserObjectPermission.objects.assign,
            "change_user", self.user, not_saved_user)
        self.assertRaises(ObjectNotPersisted,
            UserObjectPermission.objects.remove_perm,
            "change_user", self.user, not_saved_user)
        self.assertRaises(ObjectNotPersisted,
            UserObjectPermission.objects.get_for_object,
            "change_user", not_saved_user)

class GroupPermissionTests(TestCase):
    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='jack')
        self.group, created = Group.objects.get_or_create(name='jackGroup')
        self.user.groups.add(self.group)
        self.ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        self.obj1 = ContentType.objects.create(name='ct1', model='foo',
            app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(name='ct2', model='bar',
            app_label='guardian-tests')

    def test_assignement(self):
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))
        self.assertFalse(self.user.has_perm('contenttypes.change_contenttype',
            self.ctype))

        GroupObjectPermission.objects.assign('change_contenttype', self.group,
            self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
            self.ctype))

    def test_assignement_and_remove(self):
        GroupObjectPermission.objects.assign('change_contenttype', self.group,
            self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))

        GroupObjectPermission.objects.remove_perm('change_contenttype',
            self.group, self.ctype)
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))

    def test_ctypes(self):
        GroupObjectPermission.objects.assign('change_contenttype', self.group,
            self.obj1)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))

        GroupObjectPermission.objects.remove_perm('change_contenttype',
            self.group, self.obj1)
        GroupObjectPermission.objects.assign('change_contenttype', self.group,
            self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

        GroupObjectPermission.objects.assign('change_contenttype', self.group,
            self.obj1)
        GroupObjectPermission.objects.assign('change_contenttype', self.group,
            self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))

        GroupObjectPermission.objects.remove_perm('change_contenttype',
            self.group, self.obj1)
        GroupObjectPermission.objects.remove_perm('change_contenttype',
            self.group, self.obj2)
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

    def test_get_for_object(self):
        group = Group.objects.create(name='get_group_perms_for_object')
        self.user.groups.add(group)

        perms = GroupObjectPermission.objects.get_for_object(group, self.ctype)
        self.assertEqual(perms.count(), 0)

        to_assign = sorted([
            'delete_contenttype',
            'change_contenttype',
        ])

        for perm in to_assign:
            GroupObjectPermission.objects.assign(perm, group, self.ctype)

        perms = GroupObjectPermission.objects.get_for_object(group, self.ctype)
        codenames = sorted(chain(*perms.values_list('permission__codename')))

        self.assertEqual(to_assign, codenames)

    def test_assign_validation(self):
        self.assertRaises(Permission.DoesNotExist,
            GroupObjectPermission.objects.assign, 'change_user', self.group,
            self.group)

        user = User.objects.create(username='test_user_assign_validation')
        ctype = ContentType.objects.get_for_model(user)
        perm = Permission.objects.get(codename='change_group')

        create_info = dict(
            permission = perm,
            group = self.group,
            content_type = ctype,
            object_pk = user.pk
        )
        self.assertRaises(ValidationError, GroupObjectPermission.objects.create,
            **create_info)

    def test_unicode(self):
        obj_perm = GroupObjectPermission.objects.assign("change_group",
            self.group, self.group)
        self.assertTrue(isinstance(obj_perm.__unicode__(), unicode))

    def test_errors(self):
        not_saved_group = Group(name='not_saved_group')
        self.assertRaises(ObjectNotPersisted,
            GroupObjectPermission.objects.assign,
            "change_group", self.group, not_saved_group)
        self.assertRaises(ObjectNotPersisted,
            GroupObjectPermission.objects.remove_perm,
            "change_group", self.group, not_saved_group)
        self.assertRaises(ObjectNotPersisted,
            GroupObjectPermission.objects.get_for_object,
            "change_group", not_saved_group)

class ObjectPermissionBackendTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='jack')
        self.backend = ObjectPermissionBackend()

    def test_attrs(self):
        self.assertTrue(self.backend.supports_anonymous_user)
        self.assertTrue(self.backend.supports_object_permissions)
        self.assertTrue(self.backend.supports_inactive_user)

    def test_authenticate(self):
        self.assertEqual(self.backend.authenticate(
            self.user.username, self.user.password), None)

    def test_has_perm_noobj(self):
        result = self.backend.has_perm(self.user, "change_contenttype")
        self.assertFalse(result)

    def test_has_perm_notauthed(self):
        user = AnonymousUser()
        self.assertFalse(self.backend.has_perm(user, "change_user", self.user))

    def test_has_perm_wrong_app(self):
        self.assertRaises(WrongAppError, self.backend.has_perm,
            self.user, "no_app.change_user", self.user)

    def test_obj_is_not_model(self):
        for obj in (Group, 666, "String", [2, 1, 5, 7], {}):
            self.assertFalse(self.backend.has_perm(self.user,
                "any perm", obj))

    def test_not_active_user(self):
        user = User.objects.create(username='non active user')
        ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        perm = 'change_contenttype'
        UserObjectPermission.objects.assign(perm, user, ctype)
        self.assertTrue(self.backend.has_perm(user, perm, ctype))
        user.is_active = False
        user.save()
        self.assertFalse(self.backend.has_perm(user, perm, ctype))


class GuardianBaseTests(TestCase):

    def has_attrs(self):
        self.assertTrue(hasattr(guardian, '__version__'))

    def test_version(self):
        for x in guardian.VERSION:
            self.assertTrue(isinstance(x, (int, str)))

    def test_get_version(self):
        self.assertTrue(isinstance(guardian.get_version(), str))


class TestExceptions(TestCase):

    def _test_error_class(self, exc_cls):
        self.assertTrue(isinstance(exc_cls, GuardianError))

    def test_error_classes(self):
        self.assertTrue(isinstance(GuardianError(), Exception))
        guardian_errors = [NotUserNorGroup]
        for err in guardian_errors:
            self._test_error_class(err())

