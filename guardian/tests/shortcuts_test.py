from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.test import TestCase

from guardian.shortcuts import get_perms_for_model
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign
from guardian.shortcuts import remove_perm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import get_groups_with_perms
from guardian.shortcuts import get_objects_for_user
from guardian.exceptions import MixedContentTypeError
from guardian.exceptions import NotUserNorGroup
from guardian.exceptions import WrongAppError

from guardian.tests.core_test import ObjectPermissionTestCase

class ShortcutsTests(TestCase):
    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='jack')
        self.group = Group.objects.get(name='admins')

    def test_get_perms_for_model(self):
        self.assertEqual(get_perms_for_model(self.user).count(), 3)
        self.assertTrue(list(get_perms_for_model(self.user)) ==
            list(get_perms_for_model(User)))
        self.assertEqual(get_perms_for_model(Permission).count(), 3)

        model_str = 'contenttypes.ContentType'
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()),
            sorted(get_perms_for_model(ContentType).values_list()))
        obj = ContentType()
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()),
            sorted(get_perms_for_model(obj).values_list()))

class AssignTest(ObjectPermissionTestCase):
    """
    Tests permission assigning for user/group and object.
    """
    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, assign,
            perm="change_object",
            user_or_group="Not a Model",
            obj=self.ctype)

    def test_global_wrong_perm(self):
        self.assertRaises(ValueError, assign,
            perm="change_site", # for global permissions must provide app_label
            user_or_group=self.user)

    def test_user_assign(self):
        assign("change_contenttype", self.user, self.ctype)
        assign("change_contenttype", self.group, self.ctype)
        self.assertTrue(self.user.has_perm("change_contenttype", self.ctype))

    def test_group_assing(self):
        assign("change_contenttype", self.group, self.ctype)
        assign("delete_contenttype", self.group, self.ctype)

        check = ObjectPermissionChecker(self.group)
        self.assertTrue(check.has_perm("change_contenttype", self.ctype))
        self.assertTrue(check.has_perm("delete_contenttype", self.ctype))

    def test_user_assign_global(self):
        perm = assign("contenttypes.change_contenttype", self.user)
        self.assertTrue(self.user.has_perm("contenttypes.change_contenttype"))
        self.assertTrue(isinstance(perm, Permission))

    def test_group_assing_global(self):
        perm = assign("contenttypes.change_contenttype", self.group)

        self.assertTrue(self.user.has_perm("contenttypes.change_contenttype"))
        self.assertTrue(isinstance(perm, Permission))


class RemovePermTest(ObjectPermissionTestCase):
    """
    Tests object permissions removal.
    """
    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, remove_perm,
            perm="change_object",
            user_or_group="Not a Model",
            obj=self.ctype)

    def test_global_wrong_perm(self):
        self.assertRaises(ValueError, remove_perm,
            perm="change_site", # for global permissions must provide app_label
            user_or_group=self.user)

    def test_user_remove_perm(self):
        # assign perm first
        assign("change_contenttype", self.user, self.ctype)
        remove_perm("change_contenttype", self.user, self.ctype)
        self.assertFalse(self.user.has_perm("change_contenttype", self.ctype))

    def test_group_remove_perm(self):
        # assign perm first
        assign("change_contenttype", self.group, self.ctype)
        remove_perm("change_contenttype", self.group, self.ctype)

        check = ObjectPermissionChecker(self.group)
        self.assertFalse(check.has_perm("change_contenttype", self.ctype))

    def test_user_remove_perm_global(self):
        # assign perm first
        perm = "contenttypes.change_contenttype"
        assign(perm, self.user)
        remove_perm(perm, self.user)
        self.assertFalse(self.user.has_perm(perm))

    def test_group_remove_perm_global(self):
        # assign perm first
        perm = "contenttypes.change_contenttype"
        assign(perm, self.group)
        remove_perm(perm, self.group)
        app_label, codename = perm.split('.')
        perm_obj = Permission.objects.get(codename=codename,
            content_type__app_label=app_label)
        self.assertFalse(perm_obj in self.group.permissions.all())


class GetPermsTest(ObjectPermissionTestCase):
    """
    Tests get_perms function (already done at core tests but left here as a
    placeholder).
    """
    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, get_perms,
            user_or_group=None,
            obj=self.ctype)

    def test_user(self):
        perms_to_assign = ("change_contenttype",)

        for perm in perms_to_assign:
            assign("change_contenttype", self.user, self.ctype)

        perms = get_perms(self.user, self.ctype)
        for perm in perms_to_assign:
            self.assertTrue(perm in perms)

class GetUsersWithPerms(TestCase):
    """
    Tests get_users_with_perms function.
    """
    def setUp(self):
        self.obj1 = ContentType.objects.create(name='ct1', model='foo',
            app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(name='ct2', model='bar',
            app_label='guardian-tests')
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        self.group1 = Group.objects.create(name='group1')
        self.group2 = Group.objects.create(name='group2')
        self.group3 = Group.objects.create(name='group3')

    def test_empty(self):
        result = get_users_with_perms(self.obj1)
        self.assertTrue(isinstance(result, QuerySet))
        self.assertEqual(list(result), [])

        result = get_users_with_perms(self.obj1, attach_perms=True)
        self.assertTrue(isinstance(result, dict))
        self.assertFalse(bool(result))

    def test_simple(self):
        assign("change_contenttype", self.user1, self.obj1)
        assign("delete_contenttype", self.user2, self.obj1)
        assign("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1)
        result_vals = result.values_list('username', flat=True)

        self.assertEqual(
            set(result_vals),
            set([user.username for user in (self.user1, self.user2)]),
        )

    def test_users_groups_perms(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)
        assign("change_contenttype", self.group1, self.obj1)
        assign("change_contenttype", self.group2, self.obj1)
        assign("delete_contenttype", self.group3, self.obj2)

        result = get_users_with_perms(self.obj1).values_list('id',
            flat=True)
        self.assertEqual(
            set(result),
            set([u.id for u in (self.user1, self.user2)])
        )

    def test_users_groups_after_removal(self):
        self.test_users_groups_perms()
        remove_perm("change_contenttype", self.group1, self.obj1)

        result = get_users_with_perms(self.obj1).values_list('id',
            flat=True)
        self.assertEqual(
            set(result),
            set([self.user2.id]),
        )

    def test_attach_perms(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)
        assign("change_contenttype", self.group1, self.obj1)
        assign("change_contenttype", self.group2, self.obj1)
        assign("delete_contenttype", self.group3, self.obj2)
        assign("delete_contenttype", self.user2, self.obj1)
        assign("change_contenttype", self.user3, self.obj2)

        # Check contenttype1
        result = get_users_with_perms(self.obj1, attach_perms=True)
        expected = {
            self.user1: ["change_contenttype"],
            self.user2: ["change_contenttype", "delete_contenttype"],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.iteritems():
            self.assertEqual(set(perms), set(expected[key]))

        # Check contenttype2
        result = get_users_with_perms(self.obj2, attach_perms=True)
        expected = {
            self.user3: ["change_contenttype", "delete_contenttype"],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.iteritems():
            self.assertEqual(set(perms), set(expected[key]))

    def test_attach_groups_only_has_perms(self):
        self.user1.groups.add(self.group1)
        assign("change_contenttype", self.group1, self.obj1)
        result = get_users_with_perms(self.obj1, attach_perms=True)
        expected = {self.user1: ["change_contenttype"]}
        self.assertEqual(result, expected)

    def test_mixed(self):
        self.user1.groups.add(self.group1)
        assign("change_contenttype", self.group1, self.obj1)
        assign("change_contenttype", self.user2, self.obj1)
        assign("delete_contenttype", self.user2, self.obj1)
        assign("delete_contenttype", self.user2, self.obj2)
        assign("change_contenttype", self.user3, self.obj2)
        assign("change_user", self.user3, self.user1)

        result = get_users_with_perms(self.obj1)
        self.assertEqual(
            set(result),
            set([self.user1, self.user2]),
        )

class GetGroupsWithPerms(TestCase):
    """
    Tests get_groups_with_perms function.
    """
    def setUp(self):
        self.obj1 = ContentType.objects.create(name='ct1', model='foo',
            app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(name='ct2', model='bar',
            app_label='guardian-tests')
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        self.group1 = Group.objects.create(name='group1')
        self.group2 = Group.objects.create(name='group2')
        self.group3 = Group.objects.create(name='group3')

    def test_empty(self):
        result = get_groups_with_perms(self.obj1)
        self.assertTrue(isinstance(result, QuerySet))
        self.assertFalse(bool(result))

        result = get_groups_with_perms(self.obj1, attach_perms=True)
        self.assertTrue(isinstance(result, dict))
        self.assertFalse(bool(result))

    def test_simple(self):
        assign("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.group1)

    def test_simple_after_removal(self):
        self.test_simple()
        remove_perm("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1)
        self.assertEqual(len(result), 0)

    def test_simple_attach_perms(self):
        assign("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1, attach_perms=True)
        expected = {self.group1: ["change_contenttype"]}
        self.assertEqual(result, expected)

    def test_simple_attach_perms_after_removal(self):
        self.test_simple_attach_perms()
        remove_perm("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1, attach_perms=True)
        self.assertEqual(len(result), 0)

    def test_mixed(self):
        assign("change_contenttype", self.group1, self.obj1)
        assign("change_contenttype", self.group1, self.obj2)
        assign("change_user", self.group1, self.user3)
        assign("change_contenttype", self.group2, self.obj2)
        assign("change_contenttype", self.group2, self.obj1)
        assign("delete_contenttype", self.group2, self.obj1)
        assign("change_user", self.group3, self.user1)

        result = get_groups_with_perms(self.obj1)
        self.assertEqual(set(result), set([self.group1, self.group2]))

    def test_mixed_attach_perms(self):
        self.test_mixed()

        result = get_groups_with_perms(self.obj1, attach_perms=True)
        expected = {
            self.group1: ["change_contenttype"],
            self.group2: ["change_contenttype", "delete_contenttype"],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.iteritems():
            self.assertEqual(set(perms), set(expected[key]))


class GetObjectsForUser(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='joe')
        self.group = Group.objects.create(name='group')

    def test_mixed_perms(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_user,
            self.user, ['auth.change_user', 'auth.change_group'])

    def test_mixed_perms_and_klass(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_user,
            self.user, ['auth.change_group'], User)

    def test_no_app_label_nor_klass(self):
        self.assertRaises(WrongAppError, get_objects_for_user, self.user,
            ['change_group'])

    def test_empty_perms_sequence(self):
        self.assertEqual(
            set(get_objects_for_user(self.user, [], Group.objects.all())),
            set()
        )

    def test_perms_single(self):
        perm = 'auth.change_group'
        assign(perm, self.user, self.group)
        self.assertEqual(
            set(get_objects_for_user(self.user, perm)),
            set(get_objects_for_user(self.user, [perm])))

    def test_klass_as_model(self):
        assign('auth.change_group', self.user, self.group)
        objects = get_objects_for_user(self.user, ['auth.change_group'], Group)
        self.assertEqual([obj.name for obj in objects], [self.group.name])

    def test_klass_as_manager(self):
        assign('auth.change_group', self.user, self.group)
        objects = get_objects_for_user(self.user, ['auth.change_group'],
            Group.objects)
        self.assertEqual([obj.name for obj in objects], [self.group.name])

    def test_klass_as_queryset(self):
        assign('auth.change_group', self.user, self.group)
        objects = get_objects_for_user(self.user, ['auth.change_group'],
            Group.objects.all())
        self.assertEqual([obj.name for obj in objects], [self.group.name])

    def test_ensure_returns_queryset(self):
        objects = get_objects_for_user(self.user, ['auth.change_group'])
        self.assertTrue(isinstance(objects, QuerySet))

    def test_simple(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign('change_group', self.user, group)

        objects = get_objects_for_user(self.user, ['auth.change_group'])
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('name', flat=True)),
            set(group_names))

    def test_multiple_perms_to_check(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign('auth.change_group', self.user, group)
        assign('auth.delete_group', self.user, groups[1])

        objects = get_objects_for_user(self.user, ['auth.change_group',
            'auth.delete_group'])
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('name', flat=True)),
            set([groups[1].name]))

