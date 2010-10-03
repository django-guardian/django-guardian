import guardian

from itertools import chain

from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from guardian.models import UserObjectPermission
from guardian.models import GroupObjectPermission
from guardian.backends import ObjectPermissionBackend
from guardian.exceptions import GuardianError, NotUserNorGroup,\
    ObjectNotPersisted, WrongAppError

from guardian.tests.models import Keycard

class UserPermissionTests(TestCase):
    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='jack')
        self.key, created = Keycard.objects.get_or_create(key='key1')

    def test_assignement(self):
        self.assertFalse(self.user.has_perm('change_keycard', self.key))

        UserObjectPermission.objects.assign('change_keycard', self.user, self.key)
        self.assertTrue(self.user.has_perm('change_keycard', self.key))
        self.assertTrue(self.user.has_perm('guardian.change_keycard', self.key))

    def test_assignement_and_remove(self):
        UserObjectPermission.objects.assign('change_keycard', self.user, self.key)
        self.assertTrue(self.user.has_perm('change_keycard', self.key))

        UserObjectPermission.objects.remove_perm('change_keycard', self.user,
            self.key)
        self.assertFalse(self.user.has_perm('change_keycard', self.key))

    def test_keys(self):
        key1, created = Keycard.objects.get_or_create(key='keys_1')
        key2, created = Keycard.objects.get_or_create(key='keys_2')

        UserObjectPermission.objects.assign('can_use_keycard', self.user, key1)
        self.assertTrue(self.user.has_perm('can_use_keycard', key1))
        self.assertFalse(self.user.has_perm('can_use_keycard', key2))

        UserObjectPermission.objects.remove_perm('can_use_keycard', self.user, key1)
        UserObjectPermission.objects.assign('can_use_keycard', self.user, key2)
        self.assertTrue(self.user.has_perm('can_use_keycard', key2))
        self.assertFalse(self.user.has_perm('can_use_keycard', key1))

        UserObjectPermission.objects.assign('can_use_keycard', self.user, key1)
        UserObjectPermission.objects.assign('can_use_keycard', self.user, key2)
        self.assertTrue(self.user.has_perm('can_use_keycard', key2))
        self.assertTrue(self.user.has_perm('can_use_keycard', key1))

        UserObjectPermission.objects.remove_perm('can_use_keycard', self.user, key1)
        UserObjectPermission.objects.remove_perm('can_use_keycard', self.user, key2)
        self.assertFalse(self.user.has_perm('can_use_keycard', key2))
        self.assertFalse(self.user.has_perm('can_use_keycard', key1))

    def test_get_for_object(self):
        key = Keycard.objects.create(key='get_user_perms_for_object')
        perms = UserObjectPermission.objects.get_for_object(self.user, key)
        self.assertEqual(perms.count(), 0)

        to_assign = sorted([
            'delete_keycard',
            'change_keycard',
            'can_use_keycard',
            'can_suspend_keycard',
        ])

        for perm in to_assign:
            UserObjectPermission.objects.assign(perm, self.user, key)

        perms = UserObjectPermission.objects.get_for_object(self.user, key)
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
        UserObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()

    def test_assignement(self):
        key, created = Keycard.objects.get_or_create(key='nopermsyet_key')
        self.assertFalse(self.user.has_perm('change_keycard', key))
        self.assertFalse(self.user.has_perm('guardian.change_keycard', key))

        GroupObjectPermission.objects.assign('change_keycard', self.group, key)
        self.assertTrue(self.user.has_perm('change_keycard', key))
        self.assertTrue(self.user.has_perm('guardian.change_keycard', key))
        key.delete()

    def test_assignement_and_remove(self):
        key, created = Keycard.objects.get_or_create(key='some_key')
        GroupObjectPermission.objects.assign('change_keycard', self.group, key)
        self.assertTrue(self.user.has_perm('change_keycard', key))

        GroupObjectPermission.objects.remove_perm('change_keycard', self.group, key)
        self.assertFalse(self.user.has_perm('change_keycard', key))
        key.delete()

    def test_keys(self):
        key1, created = Keycard.objects.get_or_create(key='key1')
        key2, created = Keycard.objects.get_or_create(key='key2')

        GroupObjectPermission.objects.assign('can_use_keycard', self.group, key1)
        self.assertTrue(self.user.has_perm('can_use_keycard', key1))
        self.assertFalse(self.user.has_perm('can_use_keycard', key2))

        GroupObjectPermission.objects.remove_perm('can_use_keycard', self.group,
            key1)
        GroupObjectPermission.objects.assign('can_use_keycard', self.group, key2)
        self.assertTrue(self.user.has_perm('can_use_keycard', key2))
        self.assertFalse(self.user.has_perm('can_use_keycard', key1))

        GroupObjectPermission.objects.assign('can_use_keycard', self.group, key1)
        GroupObjectPermission.objects.assign('can_use_keycard', self.group, key2)
        self.assertTrue(self.user.has_perm('can_use_keycard', key2))
        self.assertTrue(self.user.has_perm('can_use_keycard', key1))

        GroupObjectPermission.objects.remove_perm('can_use_keycard', self.group,
            key1)
        GroupObjectPermission.objects.remove_perm('can_use_keycard', self.group,
            key2)
        self.assertFalse(self.user.has_perm('can_use_keycard', key2))
        self.assertFalse(self.user.has_perm('can_use_keycard', key1))

        key1.delete()
        key2.delete()

    def test_get_for_object(self):
        key = Keycard.objects.create(key='get_group_perms_for_object')
        group = Group.objects.create(name='get_group_perms_for_object')
        self.user.groups.add(group)

        perms = GroupObjectPermission.objects.get_for_object(group, key)
        self.assertEqual(perms.count(), 0)

        to_assign = sorted([
            'delete_keycard',
            'change_keycard',
            'can_use_keycard',
            'can_suspend_keycard',
        ])

        for perm in to_assign:
            GroupObjectPermission.objects.assign(perm, group, key)

        perms = GroupObjectPermission.objects.get_for_object(group, key)
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
    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='jack')
        self.backend = ObjectPermissionBackend()

    def test_attrs(self):
        self.assertTrue(self.backend.supports_anonymous_user)
        self.assertTrue(self.backend.supports_object_permissions)

    def test_authenticate(self):
        self.assertEqual(self.backend.authenticate(
            self.user.username, self.user.password), None)

    def test_has_perm_noobj(self):
        result = self.backend.has_perm(self.user, "change_key")
        self.assertFalse(result)

    def test_has_perm_notauthed(self):
        user = AnonymousUser()
        self.assertFalse(self.backend.has_perm(user, "change_user", self.user))

    def test_has_perm_wrong_app(self):
        self.assertRaises(WrongAppError, self.backend.has_perm,
            self.user, "no_app.change_user", self.user)

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

