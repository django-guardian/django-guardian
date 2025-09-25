from unittest import mock
import warnings

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.test import TestCase, TransactionTestCase

from guardian.compat import get_user_permission_full_codename
from guardian.core import ObjectPermissionChecker
from guardian.exceptions import MixedContentTypeError, MultipleIdentityAndObjectError, NotUserNorGroup, WrongAppError
from guardian.models import Group, Permission
from guardian.shortcuts import (
    _get_ct_cached,
    assign,
    assign_perm,
    copy_group_perms,
    copy_user_perms,
    get_group_perms,
    get_groups_with_perms,
    get_objects_for_group,
    get_objects_for_user,
    get_perms,
    get_perms_for_model,
    get_user_perms,
    get_users_with_perms,
    remove_perm,
    transfer_group_perms,
    transfer_user_perms,
)
from guardian.testapp.models import CharPKModel, ChildTestModel, UUIDPKModel
from guardian.testapp.tests.test_core import ObjectPermissionTestCase

User = get_user_model()
user_app_label = User._meta.app_label
user_module_name = User._meta.model_name


def get_group_content_type(obj):
    return ContentType.objects.get_for_model(Group)


class ShortcutsTests(ObjectPermissionTestCase):
    def test_get_perms_for_model(self):
        expected_perms_amount = 3 if django.VERSION < (2, 1) else 4
        self.assertEqual(get_perms_for_model(self.user).count(), expected_perms_amount)
        self.assertTrue(list(get_perms_for_model(self.user)) == list(get_perms_for_model(User)))
        self.assertEqual(get_perms_for_model(Permission).count(), expected_perms_amount)

        model_str = "contenttypes.ContentType"
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()), sorted(get_perms_for_model(ContentType).values_list())
        )
        obj = ContentType()
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()), sorted(get_perms_for_model(obj).values_list())
        )


class AssignPermTest(ObjectPermissionTestCase):
    """
    Tests permission assigning for user/group and object.
    """

    def test_not_model(self):
        self.assertRaises(
            NotUserNorGroup, assign_perm, perm="change_object", user_or_group="Not a Model", obj=self.ctype
        )

    def test_global_wrong_perm(self):
        self.assertRaises(
            ValueError,
            assign_perm,
            perm="change_site",  # for global permissions must provide app_label
            user_or_group=self.user,
        )

    def test_user_assign_perm(self):
        assign_perm("add_contenttype", self.user, self.ctype)
        assign_perm("change_contenttype", self.group, self.ctype)
        assign_perm(self.get_permission("delete_contenttype"), self.user, self.ctype)
        self.assertTrue(self.user.has_perm("add_contenttype", self.ctype))
        self.assertTrue(self.user.has_perm("change_contenttype", self.ctype))
        self.assertTrue(self.user.has_perm("delete_contenttype", self.ctype))

    def test_group_assign_perm(self):
        assign_perm("add_contenttype", self.group, self.ctype)
        assign_perm("change_contenttype", self.group, self.ctype)
        assign_perm(self.get_permission("delete_contenttype"), self.group, self.ctype)

        check = ObjectPermissionChecker(self.group)
        self.assertTrue(check.has_perm("add_contenttype", self.ctype))
        self.assertTrue(check.has_perm("change_contenttype", self.ctype))
        self.assertTrue(check.has_perm("delete_contenttype", self.ctype))

    def test_user_assign_perm_queryset(self):
        assign_perm("add_contenttype", self.user, self.ctype_qset)
        assign_perm("change_contenttype", self.group, self.ctype_qset)
        assign_perm(self.get_permission("delete_contenttype"), self.user, self.ctype_qset)
        for obj in self.ctype_qset:
            self.assertTrue(self.user.has_perm("add_contenttype", obj))
            self.assertTrue(self.user.has_perm("change_contenttype", obj))
            self.assertTrue(self.user.has_perm("delete_contenttype", obj))

    def test_group_assign_perm_queryset(self):
        assign_perm("add_contenttype", self.group, self.ctype_qset)
        assign_perm("change_contenttype", self.group, self.ctype_qset)
        assign_perm(self.get_permission("delete_contenttype"), self.group, self.ctype_qset)

        check = ObjectPermissionChecker(self.group)
        for obj in self.ctype_qset:
            self.assertTrue(check.has_perm("add_contenttype", obj))
            self.assertTrue(check.has_perm("change_contenttype", obj))
            self.assertTrue(check.has_perm("delete_contenttype", obj))

    def test_user_assign_perm_global(self):
        perm = assign_perm("contenttypes.change_contenttype", self.user)
        assign_perm(self.get_permission("delete_contenttype"), self.group)
        self.assertTrue(self.user.has_perm("contenttypes.change_contenttype"))
        self.assertTrue(self.user.has_perm("contenttypes.delete_contenttype"))
        self.assertTrue(isinstance(perm, Permission))

    def test_group_assign_perm_global(self):
        perm = assign_perm("contenttypes.change_contenttype", self.group)

        self.assertTrue(self.user.has_perm("contenttypes.change_contenttype"))
        self.assertTrue(isinstance(perm, Permission))

    def test_assign_perm_with_dots(self):
        Permission.objects.create(
            codename="contenttype.reorder", content_type=ContentType.objects.get_for_model(self.ctype)
        )

        assign_perm("contenttypes.contenttype.reorder", self.user, self.ctype)
        self.assertTrue(self.user.has_perm("contenttypes.contenttype.reorder", self.ctype))

    def test_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            assign("contenttypes.change_contenttype", self.group)
            self.assertEqual(len(warns), 1)
            self.assertTrue(isinstance(warns[0].message, DeprecationWarning))

    def test_user_assign_perm_list(self):
        """
        Test that one is able to assign permissions for a list of objects
        to a user
        """
        assign_perm("add_contenttype", self.user, self.ctype_list)
        assign_perm("change_contenttype", self.group, self.ctype_list)
        assign_perm(self.get_permission("delete_contenttype"), self.user, self.ctype_list)
        for obj in self.ctype_list:
            self.assertTrue(self.user.has_perm("add_contenttype", obj))
            self.assertTrue(self.user.has_perm("change_contenttype", obj))
            self.assertTrue(self.user.has_perm("delete_contenttype", obj))

    def test_group_assign_perm_list(self):
        """
        Test that one is able to assign permissions for a list of
        objects to a group
        """
        assign_perm("add_contenttype", self.group, self.ctype_list)
        assign_perm("change_contenttype", self.group, self.ctype_list)
        assign_perm(self.get_permission("delete_contenttype"), self.group, self.ctype_list)

        check = ObjectPermissionChecker(self.group)
        for obj in self.ctype_list:
            self.assertTrue(check.has_perm("add_contenttype", obj))
            self.assertTrue(check.has_perm("change_contenttype", obj))
            self.assertTrue(check.has_perm("delete_contenttype", obj))


class MultipleIdentitiesOperationsTest(ObjectPermissionTestCase):
    """
    Tests assignment of permission to multiple users or groups
    """

    def setUp(self):
        super().setUp()
        self.users_list = jim, bob = [
            User.objects.create_user(username="jim"),
            User.objects.create_user(username="bob"),
        ]
        self.groups_list = jim_group, bob_group = [
            Group.objects.create(name="jimgroup"),
            Group.objects.create(name="bobgroup"),
        ]
        jim_group.user_set.add(jim)
        bob_group.user_set.add(bob)
        self.users_qs = User.objects.exclude(username="AnonymousUser")
        self.groups_qs = Group.objects.all()

    def test_assign_to_many_users_queryset(self):
        assign_perm("add_contenttype", self.users_qs, self.ctype)
        assign_perm(self.get_permission("delete_contenttype"), self.users_qs, self.ctype)
        for user in self.users_list:
            self.assertTrue(user.has_perm("add_contenttype", self.ctype))
            self.assertTrue(user.has_perm("delete_contenttype", self.ctype))

    def test_assign_to_many_users_list(self):
        assign_perm("add_contenttype", self.users_list, self.ctype)
        assign_perm(self.get_permission("delete_contenttype"), self.users_list, self.ctype)
        for user in self.users_list:
            self.assertTrue(user.has_perm("add_contenttype", self.ctype))
            self.assertTrue(user.has_perm("delete_contenttype", self.ctype))

    def test_assign_to_many_groups_queryset(self):
        assign_perm("add_contenttype", self.groups_qs, self.ctype)
        assign_perm(self.get_permission("delete_contenttype"), self.groups_qs, self.ctype)
        for user in self.users_list:
            self.assertTrue(user.has_perm("add_contenttype", self.ctype))
            self.assertTrue(user.has_perm("delete_contenttype", self.ctype))

    def test_assign_to_many_groups_list(self):
        assign_perm("add_contenttype", self.groups_list, self.ctype)
        assign_perm(self.get_permission("delete_contenttype"), self.groups_list, self.ctype)
        for user in self.users_list:
            self.assertTrue(user.has_perm("add_contenttype", self.ctype))
            self.assertTrue(user.has_perm("delete_contenttype", self.ctype))

    def test_assign_to_multiple_identity_and_obj(self):
        with self.assertRaises(MultipleIdentityAndObjectError):
            assign_perm("add_contenttype", self.users_list, self.ctype_qset)
        with self.assertRaises(MultipleIdentityAndObjectError):
            assign_perm("add_contenttype", self.users_qs, self.ctype_qset)


class RemovePermTest(ObjectPermissionTestCase):
    """
    Tests object permissions removal.
    """

    def test_not_model(self):
        self.assertRaises(
            NotUserNorGroup, remove_perm, perm="change_object", user_or_group="Not a Model", obj=self.ctype
        )

    def test_global_wrong_perm(self):
        self.assertRaises(
            ValueError,
            remove_perm,
            perm="change_site",  # for global permissions must provide app_label
            user_or_group=self.user,
        )

    def test_user_remove_perm(self):
        # assign perm first
        assign_perm("change_contenttype", self.user, self.ctype)
        remove_perm("change_contenttype", self.user, self.ctype)
        self.assertFalse(self.user.has_perm("change_contenttype", self.ctype))

    def test_group_remove_perm(self):
        # assign perm first
        assign_perm("change_contenttype", self.group, self.ctype)
        remove_perm("change_contenttype", self.group, self.ctype)

        check = ObjectPermissionChecker(self.group)
        self.assertFalse(check.has_perm("change_contenttype", self.ctype))

    def test_user_remove_perm_queryset(self):
        assign_perm("change_contenttype", self.user, self.ctype_qset)
        remove_perm("change_contenttype", self.user, self.ctype_qset)
        for obj in self.ctype_qset:
            self.assertFalse(self.user.has_perm("change_contenttype", obj))

    def test_user_remove_perm_empty_queryset(self):
        assign_perm("change_contenttype", self.user, self.ctype_qset)
        remove_perm("change_contenttype", self.user, self.ctype_qset.none())

        self.assertEqual(list(self.ctype_qset.none()), [])
        for obj in self.ctype_qset:
            self.assertTrue(self.user.has_perm("change_contenttype", obj))

    def test_group_remove_perm_queryset(self):
        assign_perm("change_contenttype", self.group, self.ctype_qset)
        remove_perm("change_contenttype", self.group, self.ctype_qset)

        check = ObjectPermissionChecker(self.group)
        for obj in self.ctype_qset:
            self.assertFalse(check.has_perm("change_contenttype", obj))

    def test_user_remove_perm_global(self):
        # assign perm first
        perm = "contenttypes.change_contenttype"
        perm_obj = self.get_permission("delete_contenttype")
        assign_perm(perm, self.user)
        assign_perm(perm_obj, self.user)
        remove_perm(perm, self.user)
        remove_perm(perm_obj, self.user)
        self.assertFalse(self.user.has_perm(perm))
        self.assertFalse(self.user.has_perm(perm_obj.codename))

    def test_group_remove_perm_global(self):
        # assign perm first
        perm = "contenttypes.change_contenttype"
        assign_perm(perm, self.group)
        remove_perm(perm, self.group)
        app_label, codename = perm.split(".")
        perm_obj = Permission.objects.get(codename=codename, content_type__app_label=app_label)
        self.assertFalse(perm_obj in self.group.permissions.all())


class GetPermsTest(ObjectPermissionTestCase):
    """
    Tests get_perms function (already done at core tests but left here as a
    placeholder).
    """

    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, get_perms, user_or_group=None, obj=self.ctype)

    def test_user(self):
        perms_to_assign = ("change_contenttype",)

        for perm in perms_to_assign:
            assign_perm("change_contenttype", self.user, self.ctype)

        perms = get_perms(self.user, self.ctype)
        for perm in perms_to_assign:
            self.assertTrue(perm in perms)


class GetUsersWithPermsTest(TestCase):
    """
    Tests get_users_with_perms function.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.obj2 = ContentType.objects.create(model="bar", app_label="guardian-tests")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.user3 = User.objects.create(username="user3")
        self.group1 = Group.objects.create(name="group1")
        self.group2 = Group.objects.create(name="group2")
        self.group3 = Group.objects.create(name="group3")

    def test_empty(self):
        result = get_users_with_perms(self.obj1)
        self.assertTrue(isinstance(result, QuerySet))
        self.assertEqual(list(result), [])

        result = get_users_with_perms(self.obj1, attach_perms=True)
        self.assertTrue(isinstance(result, dict))
        self.assertFalse(bool(result))

    def test_simple(self):
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1)
        result_vals = result.values_list("username", flat=True)

        self.assertEqual(
            set(result_vals),
            {user.username for user in (self.user1, self.user2)},
        )

    def test_only_with_perms_in_groups(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group3, self.obj2)

        result = get_groups_with_perms(self.obj1, only_with_perms_in=("change_contenttype",))
        result_vals = result.values_list("name", flat=True)

        self.assertEqual(
            set(result_vals),
            {self.group1.name},
        )

    def test_only_with_perms_in_groups_attached(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group3, self.obj2)

        result = get_groups_with_perms(self.obj1, only_with_perms_in=("delete_contenttype",), attach_perms=True)

        expected = {self.group2: ("change_contenttype", "delete_contenttype")}
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))

    def test_only_with_perms_in_users(self):
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1, only_with_perms_in=("change_contenttype",))
        result_vals = result.values_list("username", flat=True)

        self.assertEqual(
            set(result_vals),
            {self.user1.username},
        )

    def test_only_with_perms_in_users_with_group_users(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)

        # assign perms to groups
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("add_contenttype", self.group3, self.obj2)

        result = get_users_with_perms(
            self.obj1, only_with_perms_in=("change_contenttype", "delete_contenttype"), with_group_users=True
        )
        result_vals = result.values_list("username", flat=True)

        self.assertEqual(
            set(result_vals),
            {self.user1.username, self.user2.username},
        )

    def test_only_with_perms_in_users_without_group_users(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)

        # assign perms to groups
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group3, self.obj2)

        # assign perms to user
        assign_perm("change_contenttype", self.user2, self.obj1)

        result = get_users_with_perms(
            self.obj1, only_with_perms_in=("change_contenttype", "delete_contenttype"), with_group_users=False
        )
        result_vals = result.values_list("username", flat=True)

        self.assertEqual(
            set(result_vals),
            {self.user2.username},
        )

    def test_only_with_perms_in_users_attached(self):
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("change_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1, only_with_perms_in=("delete_contenttype",), attach_perms=True)

        expected = {self.user2: ("change_contenttype", "delete_contenttype")}
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))

    def test_users_groups_perms(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group3, self.obj2)

        result = get_users_with_perms(self.obj1).values_list("pk", flat=True)
        self.assertEqual(set(result), {u.pk for u in (self.user1, self.user2)})

    def test_users_groups_after_removal(self):
        self.test_users_groups_perms()
        remove_perm("change_contenttype", self.group1, self.obj1)

        result = get_users_with_perms(self.obj1).values_list("pk", flat=True)
        self.assertEqual(
            set(result),
            {self.user2.pk},
        )

    def test_attach_perms(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group3, self.obj2)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("change_contenttype", self.user3, self.obj2)

        # Check contenttype1
        result = get_users_with_perms(self.obj1, attach_perms=True)
        expected = {
            self.user1: ["change_contenttype"],
            self.user2: ["change_contenttype", "delete_contenttype"],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))

        # Check contenttype2
        result = get_users_with_perms(self.obj2, attach_perms=True)
        expected = {
            self.user3: ["change_contenttype", "delete_contenttype"],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))

    def test_attach_groups_only_has_perms(self):
        self.user1.groups.add(self.group1)
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_users_with_perms(self.obj1, attach_perms=True)
        expected = {self.user1: ["change_contenttype"]}
        self.assertEqual(result, expected)

    def test_mixed(self):
        self.user1.groups.add(self.group1)
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj2)
        assign_perm("change_contenttype", self.user3, self.obj2)
        assign_perm("change_%s" % user_module_name, self.user3, self.user1)

        result = get_users_with_perms(self.obj1)
        self.assertEqual(
            set(result),
            {self.user1, self.user2},
        )

    def test_with_superusers(self):
        admin = User.objects.create(username="admin", is_superuser=True)
        assign_perm("change_contenttype", self.user1, self.obj1)

        result = get_users_with_perms(self.obj1, with_superusers=True)
        self.assertEqual(
            set(result),
            {self.user1, admin},
        )

    def test_without_group_users(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.user2, self.obj1)
        assign_perm("change_contenttype", self.group2, self.obj1)
        result = get_users_with_perms(self.obj1, with_group_users=False)
        expected = {self.user2}
        self.assertEqual(set(result), expected)

    def test_without_group_users_but_perms_attached(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.user2, self.obj1)
        assign_perm("change_contenttype", self.group2, self.obj1)
        result = get_users_with_perms(self.obj1, with_group_users=False, attach_perms=True)
        expected = {self.user2: ["change_contenttype"]}
        self.assertEqual(result, expected)

    def test_direct_perms_only(self):
        admin = User.objects.create(username="admin", is_superuser=True)
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group1)
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", admin, self.obj1)
        assign_perm("delete_contenttype", self.group1, self.obj1)
        expected = {self.user1, self.user2, admin}
        result = get_users_with_perms(self.obj1, with_superusers=False, with_group_users=True)
        self.assertEqual(set(result), expected)
        self.assertEqual(set(get_user_perms(self.user1, self.obj1)), {"change_contenttype"})
        self.assertEqual(set(get_user_perms(self.user2, self.obj1)), set())
        self.assertEqual(set(get_user_perms(admin, self.obj1)), {"delete_contenttype"})
        result = get_users_with_perms(self.obj1, with_superusers=False, with_group_users=False)
        expected = {self.user1, admin}
        self.assertEqual(set(result), expected)
        self.assertEqual(set(get_group_perms(self.user1, self.obj1)), {"delete_contenttype"})
        self.assertEqual(set(get_group_perms(self.user2, self.obj1)), {"delete_contenttype"})
        self.assertEqual(set(get_group_perms(self.group1, self.obj1)), {"delete_contenttype"})
        self.assertEqual(set(get_group_perms(self.group2, self.obj1)), set())
        self.assertEqual(set(get_group_perms(admin, self.obj1)), set())
        expected_permissions = ["add_contenttype", "change_contenttype", "delete_contenttype"]
        expected_permissions.append("view_contenttype")
        self.assertEqual(set(get_perms(admin, self.obj1)), set(expected_permissions))
        self.assertEqual(set(get_perms(self.user1, self.obj1)), {"change_contenttype", "delete_contenttype"})
        self.assertEqual(set(get_perms(self.user2, self.obj1)), {"delete_contenttype"})
        self.assertEqual(set(get_perms(self.group1, self.obj1)), {"delete_contenttype"})
        self.assertEqual(set(get_perms(self.group2, self.obj1)), set())

    def test_direct_perms_only_perms_attached(self):
        admin = User.objects.create(username="admin", is_superuser=True)
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group1)
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", admin, self.obj1)
        assign_perm("delete_contenttype", self.group1, self.obj1)
        expected = {
            self.user1: ["change_contenttype", "delete_contenttype"],
            admin: ["add_contenttype", "change_contenttype", "delete_contenttype"],
            self.user2: ["delete_contenttype"],
        }
        expected[admin].append("view_contenttype")
        result = get_users_with_perms(self.obj1, attach_perms=True, with_superusers=False, with_group_users=True)
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))
        result = get_users_with_perms(self.obj1, attach_perms=True, with_superusers=False, with_group_users=False)
        expected = {self.user1: ["change_contenttype"], admin: ["delete_contenttype"]}
        self.assertEqual(result, expected)

    def test_without_group_users_no_result(self):
        self.user1.groups.add(self.group1)
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_users_with_perms(self.obj1, attach_perms=True, with_group_users=False)
        expected = {}
        self.assertEqual(result, expected)

    def test_without_group_users_no_result_but_with_superusers(self):
        admin = User.objects.create(username="admin", is_superuser=True)
        self.user1.groups.add(self.group1)
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_users_with_perms(self.obj1, with_group_users=False, with_superusers=True)
        expected = [admin]
        self.assertEqual(set(result), set(expected))


class GetGroupsWithPerms(TestCase):
    """
    Tests get_groups_with_perms function.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.obj2 = ContentType.objects.create(model="bar", app_label="guardian-tests")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.user3 = User.objects.create(username="user3")
        self.group1 = Group.objects.create(name="group1")
        self.group2 = Group.objects.create(name="group2")
        self.group3 = Group.objects.create(name="group3")

    def test_empty(self):
        result = get_groups_with_perms(self.obj1)
        self.assertTrue(isinstance(result, QuerySet))
        self.assertFalse(bool(result))

        result = get_groups_with_perms(self.obj1, attach_perms=True)
        self.assertTrue(isinstance(result, dict))
        self.assertFalse(bool(result))

    def test_simple(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.group1)

    def test_simple_after_removal(self):
        self.test_simple()
        remove_perm("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1)
        self.assertEqual(len(result), 0)

    def test_simple_attach_perms(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1, attach_perms=True)
        expected = {self.group1: ["change_contenttype"]}
        self.assertEqual(result, expected)

    def test_simple_attach_perms_after_removal(self):
        self.test_simple_attach_perms()
        remove_perm("change_contenttype", self.group1, self.obj1)
        result = get_groups_with_perms(self.obj1, attach_perms=True)
        self.assertEqual(len(result), 0)

    def test_filter_by_contenttype(self):
        # Make sure that both objects have same pk.
        obj = ContentType.objects.create(pk=1042, model="baz", app_label="guardian-tests")
        group = Group.objects.create(pk=1042, name="group")

        assign_perm("change_group", self.group1, group)
        assign_perm("change_contenttype", self.group1, obj)

        result = get_groups_with_perms(obj, attach_perms=True)
        # No group permissions should be included, even though objects have same pk.
        self.assertEqual(result[self.group1], ["change_contenttype"])

    def test_mixed(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group1, self.obj2)
        assign_perm("change_%s" % user_module_name, self.group1, self.user3)
        assign_perm("change_contenttype", self.group2, self.obj2)
        assign_perm("change_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("change_%s" % user_module_name, self.group3, self.user1)

        result = get_groups_with_perms(self.obj1)
        self.assertEqual(set(result), {self.group1, self.group2})

    def test_mixed_attach_perms(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group1, self.obj2)
        assign_perm("change_group", self.group1, self.group3)
        assign_perm("change_contenttype", self.group2, self.obj2)
        assign_perm("change_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("change_group", self.group3, self.group1)

        result = get_groups_with_perms(self.obj1, attach_perms=True)
        expected = {
            self.group1: ["change_contenttype"],
            self.group2: ["change_contenttype", "delete_contenttype"],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))

    def test_custom_group_model(self):
        with mock.patch("guardian.conf.settings.GROUP_OBJ_PERMS_MODEL", "testapp.GenericGroupObjectPermission"):
            result = get_groups_with_perms(self.obj1)
            self.assertEqual(len(result), 0)

    def test_custom_group_model_attach_perms(self):
        with mock.patch("guardian.conf.settings.GROUP_OBJ_PERMS_MODEL", "testapp.GenericGroupObjectPermission"):
            result = get_groups_with_perms(self.obj1, attach_perms=True)
            expected = {}
            self.assertEqual(expected, result)


class GetObjectsForUser(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="joe")
        self.group = Group.objects.create(name="group")
        self.ctype = ContentType.objects.create(model="bar", app_label="fake-for-guardian-tests")

    def test_superuser(self):
        self.user.is_superuser = True
        ctypes = ContentType.objects.all()
        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"], ctypes)
        self.assertEqual(set(ctypes), set(objects))

    def test_with_superuser_true(self):
        self.user.is_superuser = True
        ctypes = ContentType.objects.all()
        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"], ctypes, with_superuser=True)
        self.assertEqual(set(ctypes), set(objects))

    def test_with_superuser_false(self):
        self.user.is_superuser = True
        ctypes = ContentType.objects.all()
        obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        assign_perm("change_contenttype", self.user, obj1)
        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"], ctypes, with_superuser=False)
        self.assertEqual({obj1}, set(objects))

    def test_anonymous(self):
        self.user = AnonymousUser()
        ctypes = ContentType.objects.all()
        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"], ctypes)

        obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        assign_perm("change_contenttype", self.user, obj1)
        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"], ctypes)
        self.assertEqual({obj1}, set(objects))

    def test_mixed_perms(self):
        codenames = [
            get_user_permission_full_codename("change"),
            "auth.change_permission",
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_user, self.user, codenames)

    def test_perms_with_mixed_apps(self):
        codenames = [
            get_user_permission_full_codename("change"),
            "contenttypes.change_contenttype",
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_user, self.user, codenames)

    def test_mixed_perms_and_klass(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_user, self.user, ["auth.change_group"], User)

    def test_override_get_content_type(self):
        with mock.patch(
            "guardian.conf.settings.GET_CONTENT_TYPE", "guardian.testapp.tests.test_shortcuts.get_group_content_type"
        ):
            get_objects_for_user(self.user, ["auth.change_group"], User)

    def test_no_app_label_nor_klass(self):
        self.assertRaises(WrongAppError, get_objects_for_user, self.user, ["change_group"])

    def test_empty_perms_sequence(self):
        objects = get_objects_for_user(self.user, [], Group.objects.all())
        self.assertEqual(set(objects), set())

    def test_perms_single(self):
        perm = "auth.change_group"
        assign_perm(perm, self.user, self.group)
        self.assertEqual(set(get_objects_for_user(self.user, perm)), set(get_objects_for_user(self.user, [perm])))

    def test_klass_as_model(self):
        assign_perm("contenttypes.change_contenttype", self.user, self.ctype)

        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"], ContentType)
        self.assertEqual([obj.name for obj in objects], [self.ctype.name])

    def test_klass_as_manager(self):
        assign_perm("auth.change_group", self.user, self.group)
        objects = get_objects_for_user(self.user, ["auth.change_group"], Group.objects)
        self.assertEqual([obj.name for obj in objects], [self.group.name])

    def test_klass_as_queryset(self):
        assign_perm("auth.change_group", self.user, self.group)
        objects = get_objects_for_user(self.user, ["auth.change_group"], Group.objects.all())
        self.assertEqual([obj.name for obj in objects], [self.group.name])

    def test_ensure_returns_queryset(self):
        objects = get_objects_for_user(self.user, ["auth.change_group"])
        self.assertTrue(isinstance(objects, QuerySet))

    def test_simple(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm("change_group", self.user, group)

        objects = get_objects_for_user(self.user, ["auth.change_group"])
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects), set(groups))

    def test_multiple_perms_to_check(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm("auth.change_group", self.user, group)
        assign_perm("auth.delete_group", self.user, groups[1])

        objects = get_objects_for_user(self.user, ["auth.change_group", "auth.delete_group"])
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("name", flat=True)), {groups[1].name})

    def test_multiple_perms_to_check_no_groups(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm("auth.change_group", self.user, group)
        assign_perm("auth.delete_group", self.user, groups[1])

        objects = get_objects_for_user(self.user, ["auth.change_group", "auth.delete_group"], use_groups=False)
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("name", flat=True)), {groups[1].name})

    def test_any_of_multiple_perms_to_check(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        assign_perm("auth.change_group", self.user, groups[0])
        assign_perm("auth.delete_group", self.user, groups[2])

        objects = get_objects_for_user(self.user, ["auth.change_group", "auth.delete_group"], any_perm=True)
        self.assertEqual(len(objects), 2)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("name", flat=True)), {groups[0].name, groups[2].name})

    def test_groups_perms(self):
        group1 = Group.objects.create(name="group1")
        group2 = Group.objects.create(name="group2")
        group3 = Group.objects.create(name="group3")
        groups = [group1, group2, group3]
        for group in groups:
            self.user.groups.add(group)

        # Objects to operate on
        ctypes = list(ContentType.objects.all().order_by("id"))
        assign_perm("auth.change_group", self.user)
        assign_perm("change_contenttype", self.user, ctypes[0])
        assign_perm("change_contenttype", self.user, ctypes[1])
        assign_perm("delete_contenttype", self.user, ctypes[1])
        assign_perm("delete_contenttype", self.user, ctypes[2])

        assign_perm("change_contenttype", groups[0], ctypes[3])
        assign_perm("change_contenttype", groups[1], ctypes[3])
        assign_perm("change_contenttype", groups[2], ctypes[4])
        assign_perm("delete_contenttype", groups[0], ctypes[0])

        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"])
        self.assertEqual(set(objects.values_list("id", flat=True)), {ctypes[i].id for i in [0, 1, 3, 4]})

        objects = get_objects_for_user(
            self.user, ["contenttypes.change_contenttype", "contenttypes.delete_contenttype"]
        )
        self.assertEqual(set(objects.values_list("id", flat=True)), {ctypes[i].id for i in [0, 1]})

        objects = get_objects_for_user(self.user, ["contenttypes.change_contenttype"])
        self.assertEqual(set(objects.values_list("id", flat=True)), {ctypes[i].id for i in [0, 1, 3, 4]})

    def test_has_global_permission_only(self):
        group_names = ["group1", "group2", "group3"]
        for name in group_names:
            Group.objects.create(name=name)
        # global permission to change any group
        perm = "auth.change_group"

        assign_perm(perm, self.user)
        objects = get_objects_for_user(self.user, perm)
        remove_perm(perm, self.user)
        self.assertEqual(set(objects), set(Group.objects.all()))

    def test_has_global_permission_and_object_based_permission(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to change any group
        perm_global = "auth.change_group"
        perm_obj = "delete_group"
        assign_perm(perm_global, self.user)
        assign_perm(perm_obj, self.user, groups[0])
        objects = get_objects_for_user(self.user, [perm_global, perm_obj])
        remove_perm(perm_global, self.user)
        self.assertEqual(set(objects.values_list("name", flat=True)), {groups[0].name})

    def test_has_global_permission_and_object_based_permission_any_perm(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to change any group
        perm_global = "auth.change_group"
        # object based permission to change only a specific group
        perm_obj = "auth.delete_group"
        assign_perm(perm_global, self.user)
        assign_perm(perm_obj, self.user, groups[0])
        objects = get_objects_for_user(self.user, [perm_global, perm_obj], any_perm=True, accept_global_perms=True)
        remove_perm(perm_global, self.user)
        self.assertEqual(set(objects), set(Group.objects.all()))

    def test_object_based_permission_without_global_permission(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to delete any group
        perm_global = "auth.delete_group"
        perm_obj = "auth.delete_group"
        assign_perm(perm_global, self.user)
        assign_perm(perm_obj, self.user, groups[0])
        objects = get_objects_for_user(self.user, [perm_obj], accept_global_perms=False)
        remove_perm(perm_global, self.user)
        self.assertEqual(set(objects.values_list("name", flat=True)), {groups[0].name})

    def test_object_based_permission_with_groups_2perms(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            self.user.groups.add(group)
        # Objects to operate on
        ctypes = list(ContentType.objects.all().order_by("id"))
        assign_perm("contenttypes.change_contenttype", self.user)
        assign_perm("change_contenttype", self.user, ctypes[0])
        assign_perm("change_contenttype", self.user, ctypes[1])
        assign_perm("delete_contenttype", self.user, ctypes[1])
        assign_perm("delete_contenttype", self.user, ctypes[2])

        assign_perm("change_contenttype", groups[0], ctypes[3])
        assign_perm("change_contenttype", groups[1], ctypes[3])
        assign_perm("change_contenttype", groups[2], ctypes[4])
        assign_perm("delete_contenttype", groups[0], ctypes[0])

        objects = get_objects_for_user(
            self.user, ["contenttypes.change_contenttype", "contenttypes.delete_contenttype"], accept_global_perms=True
        )
        self.assertEqual(set(objects.values_list("id", flat=True)), {ctypes[0].id, ctypes[1].id, ctypes[2].id})

    def test_object_based_permission_with_groups_3perms(self):
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            self.user.groups.add(group)
        # Objects to operate on
        ctypes = list(ContentType.objects.all().order_by("id"))
        assign_perm("contenttypes.change_contenttype", self.user)
        assign_perm("change_contenttype", self.user, ctypes[0])
        assign_perm("change_contenttype", self.user, ctypes[1])
        assign_perm("delete_contenttype", self.user, ctypes[1])
        assign_perm("delete_contenttype", self.user, ctypes[2])
        # add_contenttype does not make sense, here just for testing purposes,
        # to also cover one if branch in function.
        assign_perm("add_contenttype", self.user, ctypes[1])

        assign_perm("change_contenttype", groups[0], ctypes[3])
        assign_perm("change_contenttype", groups[1], ctypes[3])
        assign_perm("change_contenttype", groups[2], ctypes[4])
        assign_perm("delete_contenttype", groups[0], ctypes[0])
        assign_perm("add_contenttype", groups[0], ctypes[0])

        objects = get_objects_for_user(
            self.user,
            ["contenttypes.change_contenttype", "contenttypes.delete_contenttype", "contenttypes.add_contenttype"],
            accept_global_perms=True,
        )
        self.assertEqual(set(objects.values_list("id", flat=True)), {ctypes[0].id, ctypes[1].id})

    def test_varchar_primary_key(self):
        """
        Verify that the function works when the objects that should be returned
        have varchar primary keys.
        """
        obj_with_char_pk = CharPKModel.objects.create(char_pk="testprimarykey")
        assign_perm("add_charpkmodel", self.user, obj_with_char_pk)

        objects = get_objects_for_user(self.user, "testapp.add_charpkmodel")
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("pk", flat=True)), {obj_with_char_pk.pk})

    def test_uuid_primary_key(self):
        """
        Verify that the function works when the objects that should be returned
        have uuid primary keys.
        """
        obj_with_uuid_pk = UUIDPKModel.objects.create()
        assign_perm("add_uuidpkmodel", self.user, obj_with_uuid_pk)

        objects = get_objects_for_user(self.user, "testapp.add_uuidpkmodel")
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("pk", flat=True)), {obj_with_uuid_pk.pk})

    def test_varchar_primary_key_with_any_perm(self):
        """
        Verify that the function works with any_perm set to True when the
        objects that should be returned have varchar primary keys.
        """
        obj_with_char_pk = CharPKModel.objects.create(char_pk="testprimarykey")
        assign_perm("add_charpkmodel", self.user, obj_with_char_pk)

        objects = get_objects_for_user(
            self.user, ["testapp.add_charpkmodel", "testapp.change_charpkmodel"], any_perm=True
        )
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("pk", flat=True)), {obj_with_char_pk.pk})

    def test_uuid_primary_key_with_any_perm(self):
        """
        Verify that the function works with any_perm set to True when the
        objects that should be returned have uuid primary keys.
        """
        obj_with_uuid_pk = UUIDPKModel.objects.create()
        assign_perm("add_uuidpkmodel", self.user, obj_with_uuid_pk)

        objects = get_objects_for_user(
            self.user, ["testapp.add_uuidpkmodel", "testapp.change_uuidpkmodel"], any_perm=True
        )
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("pk", flat=True)), {obj_with_uuid_pk.pk})

    def test_varchar_primary_key_with_group_values(self):
        """
        Verify that the function works when the objects that should be returned
        have varchar primary keys, and those objects are due to the user's
        groups.
        """
        obj_with_char_pk = CharPKModel.objects.create(char_pk="testprimarykey")
        assign_perm("add_charpkmodel", self.group, obj_with_char_pk)
        self.user.groups.add(self.group)

        objects = get_objects_for_user(
            self.user, ["testapp.add_charpkmodel", "testapp.change_charpkmodel"], any_perm=True
        )
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("pk", flat=True)), {obj_with_char_pk.pk})

    def test_model_inheritance(self):
        child_with_perm = ChildTestModel.objects.create(name="child1")
        assign_perm("testapp.change_childtestmodel", self.user, child_with_perm)
        child_without_perm = ChildTestModel.objects.create(name="child2")

        children = get_objects_for_user(self.user, "testapp.change_childtestmodel", ChildTestModel)

        self.assertEqual(1, len(children))
        self.assertIn(child_with_perm, children)
        self.assertNotIn(child_without_perm, children)

    def test_uuid_primary_key_with_group_values(self):
        """
        Verify that the function works when the objects that should be returned
        have uuid primary keys, and those objects are due to the user's
        groups.
        """
        obj_with_uuid_pk = UUIDPKModel.objects.create()
        assign_perm("add_uuidpkmodel", self.group, obj_with_uuid_pk)
        self.user.groups.add(self.group)

        objects = get_objects_for_user(
            self.user, ["testapp.add_uuidpkmodel", "testapp.change_uuidpkmodel"], any_perm=True
        )
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects.values_list("pk", flat=True)), {obj_with_uuid_pk.pk})

    def test_uuid_primary_key_accept_global_perms_false_bug_fix(self):
        """
        Test for the UUID bug fix where get_objects_for_user with accept_global_perms=False
        fails to match UUID primary keys due to hyphen inconsistency.

        This test reproduces the bug described in the issue where object_pk field
        (with hyphens) was compared against transformed PKs (without hyphens).
        """
        # Create multiple UUID objects to test filtering
        obj1 = UUIDPKModel.objects.create()
        obj2 = UUIDPKModel.objects.create()
        obj3 = UUIDPKModel.objects.create()

        # Assign permissions to specific objects only
        assign_perm("add_uuidpkmodel", self.user, obj1)
        assign_perm("add_uuidpkmodel", self.user, obj2)
        # obj3 deliberately has no permissions

        # Create a queryset of all objects to pass as klass parameter
        obj_queryset = UUIDPKModel.objects.all()

        # This should only return obj1 and obj2, not obj3
        objects = get_objects_for_user(
            klass=obj_queryset,
            user=self.user,
            perms=["add_uuidpkmodel"],
            accept_global_perms=False,
        )

        # Verify correct objects are returned
        self.assertEqual(len(objects), 2)
        self.assertTrue(isinstance(objects, QuerySet))
        returned_pks = set(objects.values_list("pk", flat=True))
        expected_pks = {obj1.pk, obj2.pk}
        self.assertEqual(returned_pks, expected_pks)

        # Ensure obj3 is not included
        self.assertNotIn(obj3.pk, returned_pks)

        # Also test with groups to ensure group permissions work correctly too
        group_obj = UUIDPKModel.objects.create()
        assign_perm("add_uuidpkmodel", self.group, group_obj)
        self.user.groups.add(self.group)

        objects_with_groups = get_objects_for_user(
            klass=UUIDPKModel.objects.all(),
            user=self.user,
            perms=["add_uuidpkmodel"],
            accept_global_perms=False,
            use_groups=True,
        )

        # Should now include the group object too
        self.assertEqual(len(objects_with_groups), 3)
        group_returned_pks = set(objects_with_groups.values_list("pk", flat=True))
        expected_group_pks = {obj1.pk, obj2.pk, group_obj.pk}
        self.assertEqual(group_returned_pks, expected_group_pks)

    def test_exception_different_ctypes(self):
        self.assertRaises(
            MixedContentTypeError, get_objects_for_user, self.user, ["auth.change_permission", "auth.change_group"]
        )

    def test_has_any_permissions(self):
        # We use groups as objects.
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm("change_group", self.user, group)

        objects = get_objects_for_user(self.user, [], Group)
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects), set(groups))

    def test_short_codenames_with_klass(self):
        assign_perm("contenttypes.change_contenttype", self.user, self.ctype)

        objects = get_objects_for_user(self.user, ["change_contenttype"], ContentType)
        self.assertEqual([obj.name for obj in objects], [self.ctype.name])

    def test_has_any_group_permissions(self):
        # We use groups as objects.
        group_names = ["group1", "group2", "group3"]
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm("change_group", self.group, group)

        objects = get_objects_for_group(self.group, [], Group)
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects), set(groups))


class GetObjectsForGroup(TestCase):
    """
    Tests get_objects_for_group function.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.obj2 = ContentType.objects.create(model="bar", app_label="guardian-tests")
        self.obj3 = ContentType.objects.create(model="baz", app_label="guardian-tests")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.user3 = User.objects.create(username="user3")
        self.group1 = Group.objects.create(name="group1")
        self.group2 = Group.objects.create(name="group2")
        self.group3 = Group.objects.create(name="group3")

    def test_mixed_perms(self):
        codenames = [
            get_user_permission_full_codename("change"),
            "auth.change_permission",
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_group, self.group1, codenames)

    def test_perms_with_mixed_apps(self):
        codenames = [
            get_user_permission_full_codename("change"),
            "contenttypes.contenttypes.change_contenttype",
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_group, self.group1, codenames)

    def test_mixed_perms_and_klass(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_group, self.group1, ["auth.change_group"], User)

    def test_override_get_content_type(self):
        with mock.patch(
            "guardian.conf.settings.GET_CONTENT_TYPE", "guardian.testapp.tests.test_shortcuts.get_group_content_type"
        ):
            get_objects_for_group(self.group1, ["auth.change_group"], User)

    def test_no_app_label_nor_klass(self):
        self.assertRaises(WrongAppError, get_objects_for_group, self.group1, ["change_contenttype"])

    def test_empty_perms_sequence(self):
        self.assertEqual(set(get_objects_for_group(self.group1, [], ContentType)), set())

    def test_perms_single(self):
        perm = "contenttypes.change_contenttype"
        assign_perm(perm, self.group1, self.obj1)
        self.assertEqual(set(get_objects_for_group(self.group1, perm)), set(get_objects_for_group(self.group1, [perm])))

    def test_klass_as_model(self):
        assign_perm("contenttypes.change_contenttype", self.group1, self.obj1)

        objects = get_objects_for_group(self.group1, ["contenttypes.change_contenttype"], ContentType)
        self.assertEqual([obj.name for obj in objects], [self.obj1.name])

    def test_klass_as_manager(self):
        assign_perm("contenttypes.change_contenttype", self.group1, self.obj1)
        objects = get_objects_for_group(self.group1, ["change_contenttype"], ContentType.objects)
        self.assertEqual(list(objects), [self.obj1])

    def test_klass_as_queryset(self):
        assign_perm("contenttypes.change_contenttype", self.group1, self.obj1)
        objects = get_objects_for_group(self.group1, ["change_contenttype"], ContentType.objects.all())
        self.assertEqual(list(objects), [self.obj1])

    def test_ensure_returns_queryset(self):
        objects = get_objects_for_group(self.group1, ["contenttypes.change_contenttype"])
        self.assertTrue(isinstance(objects, QuerySet))

    def test_simple(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group1, self.obj2)

        objects = get_objects_for_group(self.group1, "contenttypes.change_contenttype")
        self.assertEqual(len(objects), 2)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(set(objects), {self.obj1, self.obj2})

    def test_simple_after_removal(self):
        self.test_simple()
        remove_perm("change_contenttype", self.group1, self.obj1)
        objects = get_objects_for_group(self.group1, "contenttypes.change_contenttype")
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.obj2)

    def test_multiple_perms_to_check(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group1, self.obj1)
        assign_perm("change_contenttype", self.group1, self.obj2)

        objects = get_objects_for_group(
            self.group1, ["contenttypes.change_contenttype", "contenttypes.delete_contenttype"]
        )
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(objects[0], self.obj1)

    def test_any_of_multiple_perms_to_check(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group1, self.obj1)
        assign_perm("add_contenttype", self.group1, self.obj2)
        assign_perm("delete_contenttype", self.group1, self.obj3)

        objects = get_objects_for_group(
            self.group1, ["contenttypes.change_contenttype", "contenttypes.delete_contenttype"], any_perm=True
        )
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual([obj for obj in objects.order_by("app_label", "id")], [self.obj1, self.obj3])

    def test_results_for_different_groups_are_correct(self):
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj2)

        self.assertEqual(set(get_objects_for_group(self.group1, "contenttypes.change_contenttype")), {self.obj1})
        self.assertEqual(set(get_objects_for_group(self.group2, "contenttypes.change_contenttype")), set())
        self.assertEqual(set(get_objects_for_group(self.group2, "contenttypes.delete_contenttype")), {self.obj2})

    def test_has_global_permission(self):
        assign_perm("contenttypes.change_contenttype", self.group1)

        objects = get_objects_for_group(self.group1, ["contenttypes.change_contenttype"])
        self.assertEqual(set(objects), set(ContentType.objects.all()))

    def test_has_global_permission_and_object_based_permission(self):
        assign_perm("contenttypes.change_contenttype", self.group1)
        assign_perm("contenttypes.delete_contenttype", self.group1, self.obj1)

        objects = get_objects_for_group(
            self.group1, ["contenttypes.change_contenttype", "contenttypes.delete_contenttype"], any_perm=False
        )
        self.assertEqual(set(objects), {self.obj1})

    def test_has_global_permission_and_object_based_permission_any_perm(self):
        assign_perm("contenttypes.change_contenttype", self.group1)
        assign_perm("contenttypes.delete_contenttype", self.group1, self.obj1)

        objects = get_objects_for_group(
            self.group1, ["contenttypes.change_contenttype", "contenttypes.delete_contenttype"], any_perm=True
        )
        self.assertEqual(set(objects), set(ContentType.objects.all()))

    def test_has_global_permission_and_object_based_permission_3perms(self):
        assign_perm("contenttypes.change_contenttype", self.group1)
        assign_perm("contenttypes.delete_contenttype", self.group1, self.obj1)
        assign_perm("contenttypes.add_contenttype", self.group1, self.obj2)

        objects = get_objects_for_group(
            self.group1,
            ["contenttypes.change_contenttype", "contenttypes.delete_contenttype", "contenttypes.add_contenttype"],
            any_perm=False,
        )
        self.assertEqual(set(objects), set())

    def test_exception_different_ctypes(self):
        self.assertRaises(
            MixedContentTypeError, get_objects_for_group, self.group1, ["auth.change_permission", "auth.change_group"]
        )


class ContentTypeCacheMixin:
    def test_first_access(self):
        shortcut_ct = _get_ct_cached("auth", "change_permission")
        ct = ContentType.objects.get_by_natural_key("auth", "permission")
        self.assertEqual(ct, shortcut_ct)

        with self.assertNumQueries(0):
            cached_ct_shortcut = _get_ct_cached("auth", "change_permission")
            cached_ct = ContentType.objects.get_by_natural_key("auth", "permission")
        self.assertEqual(cached_ct, cached_ct_shortcut)
        self.assertIs(ct, cached_ct)
        self.assertIs(shortcut_ct, cached_ct_shortcut)

    def test_second_access(self):
        shortcut_ct = _get_ct_cached("auth", "change_permission")
        ct = ContentType.objects.get_by_natural_key("auth", "permission")
        self.assertEqual(ct, shortcut_ct)

        with self.assertNumQueries(0):
            cached_ct_shortcut = _get_ct_cached("auth", "change_permission")
            cached_ct = ContentType.objects.get_by_natural_key("auth", "permission")
        self.assertEqual(cached_ct, cached_ct_shortcut)
        self.assertIs(ct, cached_ct)
        self.assertIs(shortcut_ct, cached_ct_shortcut)


class ContentTypeCacheTestCase(ContentTypeCacheMixin, TestCase):
    """Test cache against TestCase"""


class ContentTypeCacheTransactionTestCase(ContentTypeCacheMixin, TransactionTestCase):
    """Test cache against TransactionTestCase"""


class TransferGroupPermsTest(TestCase):
    """
    Tests transfer_group_perms and copy_group_perms functions.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.obj2 = ContentType.objects.create(model="bar", app_label="guardian-tests")
        self.obj3 = ContentType.objects.create(model="baz", app_label="guardian-tests")
        self.admin_group = Group.objects.create(name="Admin")
        self.manager_group = Group.objects.create(name="Manager")
        self.support_group = Group.objects.create(name="Support")

    def test_same_group_raises_error(self):
        """Test that transferring to the same group raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            transfer_group_perms(self.admin_group, self.admin_group)
        self.assertEqual(str(cm.exception), "Source and target groups cannot be the same")

    def test_transfer_all_permissions(self):
        """Test transferring all permissions from one group to another."""
        # Assign permissions to admin group
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)
        assign_perm("view_contenttype", self.admin_group, self.obj2)

        # Verify admin group has permissions
        admin_checker = ObjectPermissionChecker(self.admin_group)
        self.assertTrue(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("view_contenttype", self.obj2))

        # Transfer all permissions
        result = transfer_group_perms(self.admin_group, self.manager_group)

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 3)
        self.assertEqual(result["removed"], 3)
        self.assertEqual(result["errors"], 0)

        # Verify manager group now has permissions
        manager_checker = ObjectPermissionChecker(self.manager_group)
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(manager_checker.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(manager_checker.has_perm("view_contenttype", self.obj2))

        # Verify admin group no longer has permissions
        admin_checker = ObjectPermissionChecker(self.admin_group)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("delete_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("view_contenttype", self.obj2))

    def test_transfer_specific_permissions(self):
        """Test transferring only specific permissions."""
        # Assign permissions to admin group
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)
        assign_perm("view_contenttype", self.admin_group, self.obj2)

        # Transfer only change_contenttype permission
        result = transfer_group_perms(self.admin_group, self.manager_group, perms=["change_contenttype"])

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        # Verify manager group has only change_contenttype
        manager_checker = ObjectPermissionChecker(self.manager_group)
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(manager_checker.has_perm("delete_contenttype", self.obj1))
        self.assertFalse(manager_checker.has_perm("view_contenttype", self.obj2))

        # Verify admin group still has other permissions
        admin_checker = ObjectPermissionChecker(self.admin_group)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("view_contenttype", self.obj2))

    def test_transfer_with_full_permission_names(self):
        """Test transferring permissions using full permission names (app.codename)."""
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)

        # Transfer using full permission name
        result = transfer_group_perms(self.admin_group, self.manager_group, perms=["contenttypes.change_contenttype"])

        # Verify only change_contenttype was transferred
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        manager_checker = ObjectPermissionChecker(self.manager_group)
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(manager_checker.has_perm("delete_contenttype", self.obj1))

    def test_transfer_with_specific_objects_queryset(self):
        """Test transferring permissions for specific objects using queryset."""
        # Assign permissions to multiple objects
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("change_contenttype", self.admin_group, self.obj2)
        assign_perm("change_contenttype", self.admin_group, self.obj3)

        # Transfer permissions only for obj1 and obj2
        specific_objects = ContentType.objects.filter(id__in=[self.obj1.id, self.obj2.id])
        result = transfer_group_perms(self.admin_group, self.manager_group, klass=specific_objects)

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 2)
        self.assertEqual(result["errors"], 0)

        # Verify manager group has permissions for obj1 and obj2
        manager_checker = ObjectPermissionChecker(self.manager_group)
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj2))
        self.assertFalse(manager_checker.has_perm("change_contenttype", self.obj3))

        # Verify admin group still has permission for obj3
        admin_checker = ObjectPermissionChecker(self.admin_group)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj2))
        self.assertTrue(admin_checker.has_perm("change_contenttype", self.obj3))

    def test_transfer_without_removing_from_source(self):
        """Test transferring permissions without removing from source group."""
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)

        # Transfer without removing from source
        result = transfer_group_perms(self.admin_group, self.manager_group, remove_from_source=False)

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

        # Verify both groups have permissions
        admin_checker = ObjectPermissionChecker(self.admin_group)
        manager_checker = ObjectPermissionChecker(self.manager_group)

        self.assertTrue(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(manager_checker.has_perm("delete_contenttype", self.obj1))

    def test_copy_group_perms(self):
        """Test copy_group_perms function (should not remove from source)."""
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)

        # Copy permissions
        result = copy_group_perms(self.admin_group, self.support_group)

        # Verify copy statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

        # Verify both groups have permissions
        admin_checker = ObjectPermissionChecker(self.admin_group)
        support_checker = ObjectPermissionChecker(self.support_group)

        self.assertTrue(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(support_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(support_checker.has_perm("delete_contenttype", self.obj1))

    def test_transfer_no_permissions(self):
        """Test transferring when source group has no permissions."""
        # Don't assign any permissions to admin group
        result = transfer_group_perms(self.admin_group, self.manager_group)

        # Should have no effect
        self.assertEqual(result["transferred"], 0)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

    def test_transfer_with_existing_permissions(self):
        """Test transferring when target group already has some permissions."""
        # Assign same permission to both groups
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("change_contenttype", self.manager_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)

        result = transfer_group_perms(self.admin_group, self.manager_group)

        # Should transfer only the delete permission (change already exists)
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 2)
        self.assertEqual(result["errors"], 0)

        # Verify manager group has both permissions
        manager_checker = ObjectPermissionChecker(self.manager_group)
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(manager_checker.has_perm("delete_contenttype", self.obj1))

        # Verify admin group has no permissions
        admin_checker = ObjectPermissionChecker(self.admin_group)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("delete_contenttype", self.obj1))

    def test_transfer_with_model_class_filter(self):
        """Test transferring permissions with model class filter."""
        # Create objects of different types
        other_obj = Group.objects.create(name="test-group")

        # Assign permissions to different object types
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("change_group", self.admin_group, other_obj)

        # Transfer only ContentType permissions
        result = transfer_group_perms(self.admin_group, self.manager_group, klass=ContentType)

        # Should transfer only ContentType permission
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        # Verify manager group has ContentType permission
        manager_checker = ObjectPermissionChecker(self.manager_group)
        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(manager_checker.has_perm("change_group", other_obj))

        # Verify admin group still has Group permission
        admin_checker = ObjectPermissionChecker(self.admin_group)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("change_group", other_obj))

    def test_transfer_single_permission_string(self):
        """Test transferring with single permission as string instead of list."""
        assign_perm("change_contenttype", self.admin_group, self.obj1)
        assign_perm("delete_contenttype", self.admin_group, self.obj1)

        # Transfer single permission as string
        result = transfer_group_perms(self.admin_group, self.manager_group, perms="change_contenttype")

        # Should transfer only one permission
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        manager_checker = ObjectPermissionChecker(self.manager_group)
        admin_checker = ObjectPermissionChecker(self.admin_group)

        self.assertTrue(manager_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(manager_checker.has_perm("delete_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("delete_contenttype", self.obj1))


class TransferUserPermsTest(TestCase):
    """
    Tests transfer_user_perms and copy_user_perms functions.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.obj2 = ContentType.objects.create(model="bar", app_label="guardian-tests")
        self.obj3 = ContentType.objects.create(model="baz", app_label="guardian-tests")
        self.admin_user = User.objects.create_user(username="admin", email="admin@test.com")
        self.manager_user = User.objects.create_user(username="manager", email="manager@test.com")
        self.support_user = User.objects.create_user(username="support", email="support@test.com")

    def test_same_user_raises_error(self):
        """Test that transferring to the same user raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            transfer_user_perms(self.admin_user, self.admin_user)
        self.assertEqual(str(cm.exception), "Source and target users cannot be the same")

    def test_invalid_user_raises_error(self):
        """Test that passing invalid users raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            transfer_user_perms(None, self.manager_user)
        self.assertEqual(str(cm.exception), "Both from_user and to_user must be valid user objects")

    def test_transfer_all_permissions(self):
        """Test transferring all permissions from one user to another."""
        # Assign permissions to admin user
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)
        assign_perm("view_contenttype", self.admin_user, self.obj2)

        # Verify admin user has permissions
        self.assertTrue(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("view_contenttype", self.obj2))

        # Transfer all permissions
        result = transfer_user_perms(self.admin_user, self.manager_user)

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 3)
        self.assertEqual(result["removed"], 3)
        self.assertEqual(result["errors"], 0)

        # Verify manager user now has permissions
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.manager_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.manager_user.has_perm("view_contenttype", self.obj2))

        # Verify admin user no longer has permissions
        self.assertFalse(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.admin_user.has_perm("delete_contenttype", self.obj1))
        self.assertFalse(self.admin_user.has_perm("view_contenttype", self.obj2))

    def test_transfer_specific_permissions(self):
        """Test transferring only specific permissions."""
        # Assign permissions to admin user
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)
        assign_perm("view_contenttype", self.admin_user, self.obj2)

        # Transfer only change_contenttype permission
        result = transfer_user_perms(self.admin_user, self.manager_user, perms=["change_contenttype"])

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        # Verify manager user has only change_contenttype
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.manager_user.has_perm("delete_contenttype", self.obj1))
        self.assertFalse(self.manager_user.has_perm("view_contenttype", self.obj2))

        # Verify admin user still has other permissions
        self.assertFalse(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("view_contenttype", self.obj2))

    def test_transfer_with_full_permission_names(self):
        """Test transferring permissions using full permission names (app.codename)."""
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)

        # Transfer using full permission name
        result = transfer_user_perms(self.admin_user, self.manager_user, perms=["contenttypes.change_contenttype"])

        # Verify only change_contenttype was transferred
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.manager_user.has_perm("delete_contenttype", self.obj1))

    def test_transfer_with_specific_objects_queryset(self):
        """Test transferring permissions for specific objects using queryset."""
        # Assign permissions to multiple objects
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("change_contenttype", self.admin_user, self.obj2)
        assign_perm("change_contenttype", self.admin_user, self.obj3)

        # Transfer permissions only for obj1 and obj2
        specific_objects = ContentType.objects.filter(id__in=[self.obj1.id, self.obj2.id])
        result = transfer_user_perms(self.admin_user, self.manager_user, klass=specific_objects)

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 2)
        self.assertEqual(result["errors"], 0)

        # Verify manager user has permissions for obj1 and obj2
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj2))
        self.assertFalse(self.manager_user.has_perm("change_contenttype", self.obj3))

        # Verify admin user still has permission for obj3
        admin_checker = ObjectPermissionChecker(self.admin_user)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj2))
        self.assertTrue(admin_checker.has_perm("change_contenttype", self.obj3))

    def test_transfer_without_removing_from_source(self):
        """Test transferring permissions without removing from source user."""
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)

        # Transfer without removing from source
        result = transfer_user_perms(self.admin_user, self.manager_user, remove_from_source=False)

        # Verify transfer statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

        # Verify both users have permissions
        self.assertTrue(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.manager_user.has_perm("delete_contenttype", self.obj1))

    def test_copy_user_perms(self):
        """Test copy_user_perms function (should not remove from source)."""
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)

        # Copy permissions
        result = copy_user_perms(self.admin_user, self.support_user)

        # Verify copy statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

        # Verify both users have permissions
        self.assertTrue(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.support_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.support_user.has_perm("delete_contenttype", self.obj1))

    def test_transfer_no_permissions(self):
        """Test transferring when source user has no permissions."""
        # Don't assign any permissions to admin user
        result = transfer_user_perms(self.admin_user, self.manager_user)

        # Should have no effect
        self.assertEqual(result["transferred"], 0)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

    def test_transfer_with_existing_permissions(self):
        """Test transferring when target user already has some permissions."""
        # Assign same permission to both users
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("change_contenttype", self.manager_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)

        result = transfer_user_perms(self.admin_user, self.manager_user)

        # Should transfer only the delete permission (change already exists)
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 2)
        self.assertEqual(result["errors"], 0)

        # Verify manager user has both permissions
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.manager_user.has_perm("delete_contenttype", self.obj1))

        # Verify admin user has no permissions
        admin_checker = ObjectPermissionChecker(self.admin_user)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertFalse(admin_checker.has_perm("delete_contenttype", self.obj1))

    def test_transfer_with_model_class_filter(self):
        """Test transferring permissions with model class filter."""
        # Create objects of different types
        other_obj = Group.objects.create(name="test-group")

        # Assign permissions to different object types
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("change_group", self.admin_user, other_obj)

        # Transfer only ContentType permissions
        result = transfer_user_perms(self.admin_user, self.manager_user, klass=ContentType)

        # Should transfer only ContentType permission
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        # Verify manager user has ContentType permission
        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.manager_user.has_perm("change_group", other_obj))

        # Verify admin user still has Group permission
        admin_checker = ObjectPermissionChecker(self.admin_user)
        self.assertFalse(admin_checker.has_perm("change_contenttype", self.obj1))
        self.assertTrue(admin_checker.has_perm("change_group", other_obj))

    def test_transfer_single_permission_string(self):
        """Test transferring with single permission as string instead of list."""
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)

        # Transfer single permission as string
        result = transfer_user_perms(self.admin_user, self.manager_user, perms="change_contenttype")

        # Should transfer only one permission
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.manager_user.has_perm("delete_contenttype", self.obj1))
        self.assertFalse(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("delete_contenttype", self.obj1))

    def test_transfer_with_anonymous_user(self):
        """Test transferring permissions involving anonymous user."""
        from guardian.utils import get_anonymous_user

        anonymous_user = get_anonymous_user()

        # Assign permission to anonymous user
        assign_perm("change_contenttype", anonymous_user, self.obj1)

        # Transfer from anonymous to regular user
        result = transfer_user_perms(anonymous_user, self.admin_user)

        # Verify transfer worked
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        self.assertTrue(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(anonymous_user.has_perm("change_contenttype", self.obj1))

    def test_copy_user_perms_with_specific_perms(self):
        """Test copy_user_perms with specific permission filtering."""
        assign_perm("change_contenttype", self.admin_user, self.obj1)
        assign_perm("delete_contenttype", self.admin_user, self.obj1)
        assign_perm("view_contenttype", self.admin_user, self.obj2)

        # Copy only specific permissions
        result = copy_user_perms(self.admin_user, self.support_user, perms=["change_contenttype", "view_contenttype"])

        # Verify copy statistics
        self.assertEqual(result["transferred"], 2)
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["errors"], 0)

        # Verify admin user still has all permissions
        self.assertTrue(self.admin_user.has_perm("change_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.admin_user.has_perm("view_contenttype", self.obj2))

        # Verify support user has only copied permissions
        self.assertTrue(self.support_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.support_user.has_perm("delete_contenttype", self.obj1))
        self.assertTrue(self.support_user.has_perm("view_contenttype", self.obj2))

    def test_transfer_with_manager_klass(self):
        """Test transferring permissions with Manager as klass parameter."""
        assign_perm("change_contenttype", self.admin_user, self.obj1)

        # Transfer using Manager
        result = transfer_user_perms(self.admin_user, self.manager_user, klass=ContentType.objects)

        # Verify transfer worked
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

        self.assertTrue(self.manager_user.has_perm("change_contenttype", self.obj1))
        self.assertFalse(self.admin_user.has_perm("change_contenttype", self.obj1))


class PermissionValidationTest(TestCase):
    """
    Tests that permission copy/transfer functions validate Django's default permission system.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(model="foo", app_label="guardian-tests")
        self.admin_user = User.objects.create_user(username="admin", email="admin@test.com")
        self.manager_user = User.objects.create_user(username="manager", email="manager@test.com")
        self.admin_group = Group.objects.create(name="Admin")
        self.manager_group = Group.objects.create(name="Manager")

    def test_transfer_group_perms_with_default_system(self):
        """Test that transfer_group_perms works with default permission system."""
        # Assign permissions to admin group
        assign_perm("change_contenttype", self.admin_group, self.obj1)

        # This should work without raising any exceptions
        result = transfer_group_perms(self.admin_group, self.manager_group)

        # Verify it worked
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

    def test_transfer_user_perms_with_default_system(self):
        """Test that transfer_user_perms works with default permission system."""
        # Assign permissions to admin user
        assign_perm("change_contenttype", self.admin_user, self.obj1)

        # This should work without raising any exceptions
        result = transfer_user_perms(self.admin_user, self.manager_user)

        # Verify it worked
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["errors"], 0)

    def test_copy_group_perms_with_default_system(self):
        """Test that copy_group_perms works with default permission system."""
        # Assign permissions to admin group
        assign_perm("change_contenttype", self.admin_group, self.obj1)

        # This should work without raising any exceptions
        result = copy_group_perms(self.admin_group, self.manager_group)

        # Verify it worked
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 0)  # Copy doesn't remove
        self.assertEqual(result["errors"], 0)

    def test_copy_user_perms_with_default_system(self):
        """Test that copy_user_perms works with default permission system."""
        # Assign permissions to admin user
        assign_perm("change_contenttype", self.admin_user, self.obj1)

        # This should work without raising any exceptions
        result = copy_user_perms(self.admin_user, self.manager_user)

        # Verify it worked
        self.assertEqual(result["transferred"], 1)
        self.assertEqual(result["removed"], 0)  # Copy doesn't remove
        self.assertEqual(result["errors"], 0)

    def test_transfer_group_perms_with_custom_user_model(self):
        """Test that transfer_group_perms fails with custom user permission model."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_user_model = guardian_settings.USER_OBJ_PERMS_MODEL

        try:
            # Simulate custom user permission model
            guardian_settings.USER_OBJ_PERMS_MODEL = "myapp.CustomUserObjectPermission"

            # This should raise GuardianConfigurationError
            with self.assertRaises(GuardianConfigurationError) as cm:
                transfer_group_perms(self.admin_group, self.manager_group)

            # Verify error message
            self.assertIn("Custom user permission model detected", str(cm.exception))
            self.assertIn("myapp.CustomUserObjectPermission", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.USER_OBJ_PERMS_MODEL = original_user_model

    def test_transfer_group_perms_with_custom_group_model(self):
        """Test that transfer_group_perms fails with custom group permission model."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_group_model = guardian_settings.GROUP_OBJ_PERMS_MODEL

        try:
            # Simulate custom group permission model
            guardian_settings.GROUP_OBJ_PERMS_MODEL = "myapp.CustomGroupObjectPermission"

            # This should raise GuardianConfigurationError
            with self.assertRaises(GuardianConfigurationError) as cm:
                transfer_group_perms(self.admin_group, self.manager_group)

            # Verify error message
            self.assertIn("Custom group permission model detected", str(cm.exception))
            self.assertIn("myapp.CustomGroupObjectPermission", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.GROUP_OBJ_PERMS_MODEL = original_group_model

    def test_transfer_user_perms_with_custom_user_model(self):
        """Test that transfer_user_perms fails with custom user permission model."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_user_model = guardian_settings.USER_OBJ_PERMS_MODEL

        try:
            # Simulate custom user permission model
            guardian_settings.USER_OBJ_PERMS_MODEL = "myapp.CustomUserObjectPermission"

            # This should raise GuardianConfigurationError
            with self.assertRaises(GuardianConfigurationError) as cm:
                transfer_user_perms(self.admin_user, self.manager_user)

            # Verify error message
            self.assertIn("Custom user permission model detected", str(cm.exception))
            self.assertIn("myapp.CustomUserObjectPermission", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.USER_OBJ_PERMS_MODEL = original_user_model

    def test_transfer_user_perms_with_custom_group_model(self):
        """Test that transfer_user_perms fails with custom group permission model."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_group_model = guardian_settings.GROUP_OBJ_PERMS_MODEL

        try:
            # Simulate custom group permission model
            guardian_settings.GROUP_OBJ_PERMS_MODEL = "myapp.CustomGroupObjectPermission"

            # This should raise GuardianConfigurationError
            with self.assertRaises(GuardianConfigurationError) as cm:
                transfer_user_perms(self.admin_user, self.manager_user)

            # Verify error message
            self.assertIn("Custom group permission model detected", str(cm.exception))
            self.assertIn("myapp.CustomGroupObjectPermission", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.GROUP_OBJ_PERMS_MODEL = original_group_model

    def test_copy_group_perms_with_custom_model(self):
        """Test that copy_group_perms fails with custom permission model."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_user_model = guardian_settings.USER_OBJ_PERMS_MODEL

        try:
            # Simulate custom user permission model
            guardian_settings.USER_OBJ_PERMS_MODEL = "myapp.CustomUserObjectPermission"

            # This should raise GuardianConfigurationError since copy_group_perms calls transfer_group_perms
            with self.assertRaises(GuardianConfigurationError) as cm:
                copy_group_perms(self.admin_group, self.manager_group)

            # Verify error message
            self.assertIn("Custom user permission model detected", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.USER_OBJ_PERMS_MODEL = original_user_model

    def test_copy_user_perms_with_custom_model(self):
        """Test that copy_user_perms fails with custom permission model."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_group_model = guardian_settings.GROUP_OBJ_PERMS_MODEL

        try:
            # Simulate custom group permission model
            guardian_settings.GROUP_OBJ_PERMS_MODEL = "myapp.CustomGroupObjectPermission"

            # This should raise GuardianConfigurationError since copy_user_perms calls transfer_user_perms
            with self.assertRaises(GuardianConfigurationError) as cm:
                copy_user_perms(self.admin_user, self.manager_user)

            # Verify error message
            self.assertIn("Custom group permission model detected", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.GROUP_OBJ_PERMS_MODEL = original_group_model

    def test_validation_error_message_content(self):
        """Test that validation error messages are informative."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_user_model = guardian_settings.USER_OBJ_PERMS_MODEL

        try:
            # Simulate custom user permission model
            guardian_settings.USER_OBJ_PERMS_MODEL = "myapp.CustomUserObjectPermission"

            with self.assertRaises(GuardianConfigurationError) as cm:
                transfer_group_perms(self.admin_group, self.manager_group)

            error_message = str(cm.exception)

            # Verify error message contains all important information
            self.assertIn(
                "Permission copy/transfer functions only work with Django's default permission system", error_message
            )
            self.assertIn("myapp.CustomUserObjectPermission", error_message)
            self.assertIn("standard django-guardian permission model structure", error_message)
            self.assertIn("may not work correctly with custom permission models", error_message)

        finally:
            # Restore original settings
            guardian_settings.USER_OBJ_PERMS_MODEL = original_user_model

    def test_both_custom_models_detected(self):
        """Test that validation detects custom models in the order they are checked."""
        from guardian.conf import settings as guardian_settings
        from guardian.exceptions import GuardianConfigurationError

        # Store original settings
        original_user_model = guardian_settings.USER_OBJ_PERMS_MODEL
        original_group_model = guardian_settings.GROUP_OBJ_PERMS_MODEL

        try:
            # Set both custom models
            guardian_settings.USER_OBJ_PERMS_MODEL = "myapp.CustomUserObjectPermission"
            guardian_settings.GROUP_OBJ_PERMS_MODEL = "myapp.CustomGroupObjectPermission"

            # Should fail on the first check (user model)
            with self.assertRaises(GuardianConfigurationError) as cm:
                transfer_group_perms(self.admin_group, self.manager_group)

            # Should mention user model first since it's checked first
            self.assertIn("Custom user permission model detected", str(cm.exception))
            self.assertIn("myapp.CustomUserObjectPermission", str(cm.exception))

        finally:
            # Restore original settings
            guardian_settings.USER_OBJ_PERMS_MODEL = original_user_model
            guardian_settings.GROUP_OBJ_PERMS_MODEL = original_group_model
