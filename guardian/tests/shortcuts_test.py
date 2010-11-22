from django.contrib.auth.models import User, Group, Permission
from django.contrib.flatpages.models import FlatPage
from django.db.models.query import QuerySet
from django.test import TestCase

from guardian.shortcuts import get_perms_for_model
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign
from guardian.shortcuts import remove_perm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import get_groups_with_perms
from guardian.exceptions import NotUserNorGroup

from guardian.tests.app.models import Keycard
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

        model_str = 'guardian.Keycard'
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()),
            sorted(get_perms_for_model(Keycard).values_list()))
        key = Keycard()
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()),
            sorted(get_perms_for_model(key).values_list()))

class AssignTest(ObjectPermissionTestCase):
    """
    Tests permission assigning for user/group and object.
    """
    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, assign,
            perm="change_object",
            user_or_group="Not a Model",
            obj=self.flatpage)

    def test_user_assign(self):
        assign("change_flatpage", self.user, self.flatpage)
        assign("change_flatpage", self.group, self.flatpage)
        self.assertTrue(self.user.has_perm("change_flatpage", self.flatpage))

    def test_group_assing(self):
        assign("change_flatpage", self.group, self.flatpage)
        assign("delete_flatpage", self.group, self.flatpage)

        check = ObjectPermissionChecker(self.group)
        self.assertTrue(check.has_perm("change_flatpage", self.flatpage))
        self.assertTrue(check.has_perm("delete_flatpage", self.flatpage))

class RemovePermTest(ObjectPermissionTestCase):
    """
    Tests object permissions removal.
    """
    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, remove_perm,
            perm="change_object",
            user_or_group="Not a Model",
            obj=self.flatpage)

    def test_user_remove_perm(self):
        # assign perm first
        assign("change_flatpage", self.user, self.flatpage)
        remove_perm("change_flatpage", self.user, self.flatpage)
        self.assertFalse(self.user.has_perm("change_flatpage", self.flatpage))

    def test_group_remove_perm(self):
        # assign perm first
        assign("change_flatpage", self.group, self.flatpage)
        remove_perm("change_flatpage", self.group, self.flatpage)

        check = ObjectPermissionChecker(self.group)
        self.assertFalse(check.has_perm("change_flatpage", self.flatpage))

class GetPermsTest(ObjectPermissionTestCase):
    """
    Tests get_perms function (already done at core tests but left here as a
    placeholder).
    """
    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, get_perms,
            user_or_group=None,
            obj=self.flatpage)

    def test_user(self):
        perms_to_assign = ("change_flatpage",)

        for perm in perms_to_assign:
            assign("change_flatpage", self.user, self.flatpage)

        perms = get_perms(self.user, self.flatpage)
        for perm in perms_to_assign:
            self.assertTrue(perm in perms)

class GetUsersWithPerms(TestCase):
    """
    Tests get_users_with_perms function.
    """
    def setUp(self):
        self.flatpage1 = FlatPage.objects.create(title='page1', url='/page1/')
        self.flatpage2 = FlatPage.objects.create(title='page2', url='/page2/')
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        self.group1 = Group.objects.create(name='group1')
        self.group2 = Group.objects.create(name='group2')
        self.group3 = Group.objects.create(name='group3')

    def test_empty(self):
        result = get_users_with_perms(self.flatpage1)
        self.assertTrue(isinstance(result, QuerySet))
        self.assertEqual(list(result), [])

        result = get_users_with_perms(self.flatpage1, attach_perms=True)
        self.assertTrue(isinstance(result, dict))
        self.assertFalse(bool(result))

    def test_simple(self):
        assign("change_flatpage", self.user1, self.flatpage1)
        assign("delete_flatpage", self.user2, self.flatpage1)
        assign("delete_flatpage", self.user3, self.flatpage2)

        result = get_users_with_perms(self.flatpage1)
        result_vals = result.values_list('username', flat=True)

        self.assertEqual(
            set(result_vals),
            set([user.username for user in (self.user1, self.user2)]),
        )

    def test_users_groups_perms(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)
        assign("change_flatpage", self.group1, self.flatpage1)
        assign("change_flatpage", self.group2, self.flatpage1)
        assign("delete_flatpage", self.group3, self.flatpage2)

        result = get_users_with_perms(self.flatpage1).values_list('id',
            flat=True)
        self.assertEqual(
            set(result),
            set([u.id for u in (self.user1, self.user2)])
        )

    def test_users_groups_after_removal(self):
        self.test_users_groups_perms()
        remove_perm("change_flatpage", self.group1, self.flatpage1)

        result = get_users_with_perms(self.flatpage1).values_list('id',
            flat=True)
        self.assertEqual(
            set(result),
            set([self.user2.id]),
        )

    def test_attach_perms(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)
        assign("change_flatpage", self.group1, self.flatpage1)
        assign("change_flatpage", self.group2, self.flatpage1)
        assign("delete_flatpage", self.group3, self.flatpage2)
        assign("delete_flatpage", self.user2, self.flatpage1)
        assign("change_flatpage", self.user3, self.flatpage2)

        # Check flatpage1
        result = get_users_with_perms(self.flatpage1, attach_perms=True)
        should_by = {
            self.user1: ["change_flatpage"],
            self.user2: ["change_flatpage", "delete_flatpage"],
        }
        self.assertEqual(result, should_by)

        # Check flatpage2
        result = get_users_with_perms(self.flatpage2, attach_perms=True)
        should_by = {
            self.user3: ["change_flatpage", "delete_flatpage"],
        }
        self.assertEqual(result, should_by)

    def test_attach_groups_only_has_perms(self):
        self.user1.groups.add(self.group1)
        assign("change_flatpage", self.group1, self.flatpage1)
        result = get_users_with_perms(self.flatpage1, attach_perms=True)
        should_be = {self.user1: ["change_flatpage"]}
        self.assertEqual(result, should_be)

    def test_mixed(self):
        self.user1.groups.add(self.group1)
        assign("change_flatpage", self.group1, self.flatpage1)
        assign("change_flatpage", self.user2, self.flatpage1)
        assign("delete_flatpage", self.user2, self.flatpage1)
        assign("delete_flatpage", self.user2, self.flatpage2)
        assign("change_flatpage", self.user3, self.flatpage2)
        assign("change_user", self.user3, self.user1)

        result = get_users_with_perms(self.flatpage1)
        self.assertEqual(
            set(result),
            set([self.user1, self.user2]),
        )

class GetGroupsWithPerms(TestCase):
    """
    Tests get_groups_with_perms function.
    """
    def setUp(self):
        self.flatpage1 = FlatPage.objects.create(title='page1', url='/page1/')
        self.flatpage2 = FlatPage.objects.create(title='page2', url='/page2/')
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        self.group1 = Group.objects.create(name='group1')
        self.group2 = Group.objects.create(name='group2')
        self.group3 = Group.objects.create(name='group3')

    def test_empty(self):
        result = get_groups_with_perms(self.flatpage1)
        self.assertTrue(isinstance(result, QuerySet))
        self.assertFalse(bool(result))

        result = get_groups_with_perms(self.flatpage1, attach_perms=True)
        self.assertTrue(isinstance(result, dict))
        self.assertFalse(bool(result))

    def test_simple(self):
        assign("change_flatpage", self.group1, self.flatpage1)
        result = get_groups_with_perms(self.flatpage1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.group1)

    def test_simple_after_removal(self):
        self.test_simple()
        remove_perm("change_flatpage", self.group1, self.flatpage1)
        result = get_groups_with_perms(self.flatpage1)
        self.assertEqual(len(result), 0)

    def test_simple_attach_perms(self):
        assign("change_flatpage", self.group1, self.flatpage1)
        result = get_groups_with_perms(self.flatpage1, attach_perms=True)
        expected = {self.group1: ["change_flatpage"]}
        self.assertEqual(result, expected)

    def test_simple_attach_perms_after_removal(self):
        self.test_simple_attach_perms()
        remove_perm("change_flatpage", self.group1, self.flatpage1)
        result = get_groups_with_perms(self.flatpage1, attach_perms=True)
        self.assertEqual(len(result), 0)

    def test_mixed(self):
        assign("change_flatpage", self.group1, self.flatpage1)
        assign("change_flatpage", self.group1, self.flatpage2)
        assign("change_user", self.group1, self.user3)
        assign("change_flatpage", self.group2, self.flatpage2)
        assign("change_flatpage", self.group2, self.flatpage1)
        assign("delete_flatpage", self.group2, self.flatpage1)
        assign("change_user", self.group3, self.user1)

        result = get_groups_with_perms(self.flatpage1)
        self.assertEqual(set(result), set([self.group1, self.group2]))

    def test_mixed_attach_perms(self):
        self.test_mixed()

        result = get_groups_with_perms(self.flatpage1, attach_perms=True)
        expected = {
            self.group1: ["change_flatpage"],
            self.group2: ["change_flatpage", "delete_flatpage"],
        }
        self.assertEqual(result, expected)

