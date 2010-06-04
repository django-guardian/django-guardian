from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission

from guardian.shortcuts import get_perms_for_model
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign, remove_perm, get_perms
from guardian.exceptions import NotUserNorGroup

from guardian.tests.models import Keycard
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

