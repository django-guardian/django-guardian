import warnings

import django
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.test import TestCase

from guardian.shortcuts import get_perms_for_model, bulk_assign_perms, bulk_remove_perms, commit_object_perms
from guardian.core import ObjectPermissionChecker
from guardian.compat import get_user_permission_full_codename
from guardian.shortcuts import assign
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_user_perms
from guardian.shortcuts import get_group_perms
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import get_groups_with_perms
from guardian.shortcuts import get_objects_for_user
from guardian.shortcuts import get_objects_for_group
from guardian.exceptions import MixedContentTypeError
from guardian.exceptions import NotUserNorGroup
from guardian.exceptions import WrongAppError
from guardian.exceptions import MultipleIdentityAndObjectError
from guardian.testapp.models import CharPKModel, ChildTestModel, UUIDPKModel, Project, Post, ModelWithBinaryField
from guardian.testapp.tests.test_core import ObjectPermissionTestCase
from guardian.models import Group, Permission
from guardian.utils import get_identity

User = get_user_model()
user_app_label = User._meta.app_label
user_module_name = User._meta.model_name


class ShortcutsTests(ObjectPermissionTestCase):

    def test_get_perms_for_model(self):
        expected_perms_amount = 3 if django.VERSION < (2, 1) else 4
        self.assertEqual(get_perms_for_model(self.user).count(), expected_perms_amount)
        self.assertTrue(list(get_perms_for_model(self.user)) ==
                        list(get_perms_for_model(User)))
        self.assertEqual(get_perms_for_model(Permission).count(), expected_perms_amount)

        model_str = 'contenttypes.ContentType'
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()),
            sorted(get_perms_for_model(ContentType).values_list()))
        obj = ContentType()
        self.assertEqual(
            sorted(get_perms_for_model(model_str).values_list()),
            sorted(get_perms_for_model(obj).values_list()))


class AssignPermTest(ObjectPermissionTestCase):
    """
    Tests permission assigning for user/group and object.
    """

    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, assign_perm,
                          perm="change_object",
                          user_or_group="Not a Model",
                          obj=self.ctype)

    def test_global_wrong_perm(self):
        self.assertRaises(ValueError, assign_perm,
                          perm="change_site",  # for global permissions must provide app_label
                          user_or_group=self.user)

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
            codename="contenttype.reorder",
            content_type=ContentType.objects.get_for_model(self.ctype)
        )

        assign_perm("contenttypes.contenttype.reorder", self.user, self.ctype)
        self.assertTrue(self.user.has_perm("contenttypes.contenttype.reorder", self.ctype))

    def test_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter('always')
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
            User.objects.create_user(username='jim'),
            User.objects.create_user(username='bob')
        ]
        self.groups_list = jim_group, bob_group = [
            Group.objects.create(name='jimgroup'),
            Group.objects.create(name='bobgroup')
        ]
        jim_group.user_set.add(jim)
        bob_group.user_set.add(bob)
        self.users_qs = User.objects.exclude(username='AnonymousUser')
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


class BulkPermTestBase(ObjectPermissionTestCase):
    def setUp(self):
        super().setUp()
        self.extra_objs = [
            ContentType.objects.create(model='extra%s' % i, app_label='fake-for-guardian-tests') for i in range(3)
        ]
        self.all_objects = [
            self.ctype,
            *self.extra_objs
        ]
        self.group_2, created = Group.objects.get_or_create(name='johnGroup')
        self.user_2, created = User.objects.get_or_create(username='john')
        self.user_2.groups.add(self.group_2)
        self.all_auth_entities = set([self.group, self.user, self.group_2, self.user_2])

    def clear_users_perms_caches(self, users):
        for user in users:
            for attr in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
                if hasattr(user, attr):
                    delattr(user, attr)

    def _get_unaffected_entities(self, affected_entities):
        unaffected_entities = []
        if self.group not in affected_entities:
            if self.user in affected_entities:
                unaffected_entities.append(self.group)
            else:
                unaffected_entities.append(self.user)
                unaffected_entities.append(self.group)

        if self.group_2 not in affected_entities:
            if self.user_2 in affected_entities:
                unaffected_entities.append(self.group_2)
            else:
                unaffected_entities.append(self.user_2)
                unaffected_entities.append(self.group_2)

        return unaffected_entities

    def _check_auth_entities_perms_on_objs(self, auth_entities, objs, perms_iterable, have_perms):
        assertion = self.assertTrue if have_perms else self.assertFalse
        for auth_ent in auth_entities:
            checker = ObjectPermissionChecker(auth_ent)
            checker.prefetch_perms(objs)
            for o in objs:
                for perm in perms_iterable:
                    assertion(
                        checker.has_perm(perm, o)
                    )


class BulkAssignPermTest(BulkPermTestBase):
    """
    Tests the bulk_assign_perms shortcut.
    Would be much easier to test using parametrize, but this is incompatible with unittest
    """

    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, bulk_assign_perms,
                          perms="change_object",
                          user_or_group="Not a Model",
                          obj=self.ctype)

    def test_global_wrong_perm(self):
        self.assertRaises(ValueError, bulk_assign_perms,
                          perms="change_site",  # for global permissions must provide app_label
                          user_or_group=self.user)

    def _test_bulk_add_global_perms(self, multiple_perms, multi_user_or_group, auth_type):
        auth_entity_to_user = dict()
        if auth_type == "user":
            auth_entity_or_entities_iterable = [self.user]
            auth_entity_to_user[self.user] = self.user
            if multi_user_or_group:
                user_2, created = User.objects.get_or_create(username='john')
                auth_entity_or_entities_iterable.append(user_2)
                auth_entity_to_user[user_2] = user_2
        else:
            auth_entity_or_entities_iterable = [self.group]
            auth_entity_to_user[self.group] = self.user
            if multi_user_or_group:
                group_2, created = Group.objects.get_or_create(name='johnGroup')
                user_2, created = User.objects.get_or_create(username='john')
                user_2.groups.add(group_2)
                auth_entity_or_entities_iterable.append(group_2)
                auth_entity_to_user[group_2] = user_2

        # we store this variable to test both cases, an iterable and a single object argument
        if len(auth_entity_or_entities_iterable) > 1:
            auth_entity_or_entities = auth_entity_or_entities_iterable
        else:
            auth_entity_or_entities = auth_entity_or_entities_iterable[0]

        all_perms = ["contenttypes.add_contenttype", "contenttypes.change_contenttype",
                     "contenttypes.delete_contenttype"]
        # we store this variable to test both cases, an iterable and a single object argument
        if multiple_perms:
            perms = all_perms
        else:
            perms = "contenttypes.change_contenttype"

        perms_iterable = perms if isinstance(perms, (list, QuerySet)) else [perms]
        bulk_assign_perms(perms, auth_entity_or_entities)
        for auth_ent in auth_entity_or_entities_iterable:
            user = auth_entity_to_user[auth_ent]
            for perm in perms_iterable:
                self.assertTrue(
                    user.has_perm(perm)
                )

    def test_assign_single_global_perm_from_single_user(self):
        self._test_bulk_add_global_perms(False, False, "user")

    def test_assign_single_global_perm_from_multiple_users(self):
        self._test_bulk_add_global_perms(False, True, "user")

    def test_assign_multiple_global_perms_from_single_user(self):
        self._test_bulk_add_global_perms(True, False, "user")

    def test_assign_multiple_global_perm_from_multiple_users(self):
        self._test_bulk_add_global_perms(True, True, "user")

    def test_assign_single_global_perm_from_single_group(self):
        self._test_bulk_add_global_perms(False, False, "group")

    def test_assign_single_global_perm_from_multiple_groups(self):
        self._test_bulk_add_global_perms(False, True, "group")

    def test_assign_multiple_global_perms_from_single_group(self):
        self._test_bulk_add_global_perms(True, False, "group")

    def test_assign_multiple_global_perm_from_multiple_groups(self):
        self._test_bulk_add_global_perms(True, True, "group")

    def _setup_bulk_assign_test(
            self,
            perms_to_add,
            affected_auth_entities,
            obj,
    ):
        if len(affected_auth_entities) > 1:
            auth_entity_or_entities = affected_auth_entities.copy()
        else:
            auth_entity_or_entities = affected_auth_entities[0]

        all_affected_auth_entities = affected_auth_entities.copy()
        for auth_entity in affected_auth_entities:
            user, group = get_identity(auth_entity)
            if group:
                all_affected_auth_entities.extend(list(group.user_set.all()))

        obj_iterable = obj if isinstance(obj, (list, QuerySet)) else [obj]
        perms_iterable = perms_to_add if isinstance(perms_to_add, (list, QuerySet)) else [perms_to_add]

        return (
            auth_entity_or_entities,
            all_affected_auth_entities,
            obj_iterable,
            perms_iterable
        )

    def test_no_commit(self):
        affected_auth_entities = [self.group]
        unaffected_auth_entities = [self.group_2, self.user_2]
        obj_iterable = [self.ctype, self.extra_objs[0]]
        unaffected_extra_objs = self.extra_objs[1:]

        all_contenttype_perms = ["view_contenttype", "add_contenttype", "change_contenttype", "delete_contenttype"]
        perms_to_add_1 = all_contenttype_perms[:2]
        perms_to_add_2 = all_contenttype_perms[2:3]
        all_assigned_perms = perms_to_add_1 + perms_to_add_2
        perms_not_assigned = all_contenttype_perms[3:]

        uncommitted_perms = bulk_assign_perms(perms_to_add_1, affected_auth_entities, obj_iterable, commit=False)
        uncommitted_perms.extend(
            bulk_assign_perms(perms_to_add_2, affected_auth_entities, obj_iterable, commit=False)
        )

        self._check_auth_entities_perms_on_objs(
            affected_auth_entities,
            obj_iterable,
            all_contenttype_perms,
            have_perms=False
        )

        commit_object_perms(uncommitted_perms, for_groups=True, obj=obj_iterable)

        self._check_auth_entities_perms_on_objs(
            affected_auth_entities,
            obj_iterable,
            all_assigned_perms,
            have_perms=True
        )
        self._check_auth_entities_perms_on_objs(
            affected_auth_entities,
            obj_iterable,
            perms_not_assigned,
            have_perms=False
        )

        self._check_auth_entities_perms_on_objs(
            affected_auth_entities,
            unaffected_extra_objs,
            all_contenttype_perms,
            have_perms=False
        )

        self._check_auth_entities_perms_on_objs(
            unaffected_auth_entities,
            [*obj_iterable, *unaffected_extra_objs],
            all_contenttype_perms,
            have_perms=False
        )

    def _test_bulk_add_object_perms(
            self,
            perms_to_add,
            affected_auth_entities,
            obj,
            unaffected_extra_objs
    ):
        if len(affected_auth_entities) > 1:
            auth_entity_or_entities = affected_auth_entities.copy()
        else:
            auth_entity_or_entities = affected_auth_entities[0]

        all_affected_auth_entities = affected_auth_entities.copy()
        for auth_entity in affected_auth_entities:
            user, group = get_identity(auth_entity)
            if group:
                all_affected_auth_entities.extend(list(group.user_set.all()))

        obj_iterable = obj if isinstance(obj, (list, QuerySet)) else [obj]

        all_contenttype_perms = ["view_contenttype", "add_contenttype", "change_contenttype", "delete_contenttype"]
        perms_to_add_iterable = perms_to_add if isinstance(perms_to_add, (list, QuerySet)) else [perms_to_add]
        perms_not_assigned = list(set(all_contenttype_perms) - set(perms_to_add_iterable))

        bulk_assign_perms(perms_to_add, auth_entity_or_entities, obj)
        self._check_auth_entities_perms_on_objs(
            affected_auth_entities,
            obj_iterable,
            perms_to_add_iterable,
            have_perms=True
        )
        self._check_auth_entities_perms_on_objs(
            affected_auth_entities,
            obj_iterable,
            perms_not_assigned,
            have_perms=False
        )

        if unaffected_extra_objs:
            self._check_auth_entities_perms_on_objs(
                affected_auth_entities,
                unaffected_extra_objs,
                all_contenttype_perms,
                have_perms=False
            )

        unaffected_auth_entities = self._get_unaffected_entities(affected_auth_entities)
        self._check_auth_entities_perms_on_objs(
            unaffected_auth_entities,
            [*obj_iterable, *(unaffected_extra_objs or [])],
            all_contenttype_perms,
            have_perms=False
        )

    def test_assign_single_perm_from_single_user_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.user],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_single_perm_from_single_user_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.user],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_single_perm_from_single_user_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.user],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_single_perm_from_multiple_users_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_single_perm_from_multiple_users_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.user, self.user_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_single_perm_from_multiple_users_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_single_perm_from_single_group_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.group],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_single_perm_from_single_group_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.group],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_single_perm_from_single_group_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.group],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_single_perm_from_multiple_groups_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_single_perm_from_multiple_groups_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.group, self.group_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_single_perm_from_multiple_groups_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add="change_contenttype",
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_multiple_perms_from_single_user_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_multiple_perms_from_single_user_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_multiple_perms_from_single_user_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_multiple_perms_from_multiple_users_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_multiple_perms_from_multiple_users_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user, self.user_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_multiple_perms_from_multiple_users_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_multiple_perms_from_single_group_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_multiple_perms_from_single_group_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_multiple_perms_from_single_group_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_assign_multiple_perms_from_multiple_groups_for_single_obj(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_assign_multiple_perms_from_multiple_groups_for_list(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group, self.group_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_assign_multiple_perms_from_multiple_groups_for_queryset(self):
        self._test_bulk_add_object_perms(
            perms_to_add=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_add_when_multiple_models_with_same_perm(self):
        """
        The reason this is tested is because there was a bug in this case.
        The scenario is that we have a permission with a certain name (here "add_post") that exists on two models in
        the same app.
        """
        assert ContentType.objects.get(model="post")
        project_ctype = ContentType.objects.get(model="project")
        Permission.objects.create(
            codename='add_post',
            name='Can add post',
            content_type=project_ctype
        )
        post = Post.objects.create(title='Post1')
        project = Project.objects.create(name='Project1')
        auth_entities = [self.group, self.group_2]
        perms_to_add = ["add_post"]

        self._test_bulk_add_object_perms(
            perms_to_add=perms_to_add,
            affected_auth_entities=auth_entities,
            obj=[project],
            unaffected_extra_objs=[],
        )

        # in addition to the checks done above, test that auth_entities do not have add_post on the post object (since
        # bulk_assign_perms was called on the project)
        self._check_auth_entities_perms_on_objs(
            auth_entities,
            [post],
            perms_to_add,
            have_perms=False
        )


class BulkRemovePermTest(BulkPermTestBase):
    """
    Tests the bulk_remove_perms shortcut.
    Would be much easier to test using parametrize, but this is incompatible with unittest
    """

    def test_not_model(self):
        self.assertRaises(NotUserNorGroup, bulk_remove_perms,
                          perms="change_object",
                          user_or_group_or_iterable="Not a Model",
                          obj=self.ctype)

    def test_global_wrong_perm(self):
        self.assertRaises(ValueError, bulk_remove_perms,
                          perms="change_site",  # for global permissions must provide app_label
                          user_or_group_or_iterable=self.user)

    def _test_bulk_remove_global_perms(self, multiple_perms, multi_user_or_group, auth_type):
        auth_entity_to_user = dict()
        if auth_type == "user":
            auth_entity_or_entities_iterable = [self.user]
            auth_entity_to_user[self.user] = self.user
            if multi_user_or_group:
                user_2, created = User.objects.get_or_create(username='john')
                auth_entity_or_entities_iterable.append(user_2)
                auth_entity_to_user[user_2] = user_2
        else:
            auth_entity_or_entities_iterable = [self.group]
            auth_entity_to_user[self.group] = self.user
            if multi_user_or_group:
                group_2, created = Group.objects.get_or_create(name='johnGroup')
                user_2, created = User.objects.get_or_create(username='john')
                user_2.groups.add(group_2)
                auth_entity_or_entities_iterable.append(group_2)
                auth_entity_to_user[group_2] = user_2

        # we store this variable to test both cases, an iterable and a single object argument
        if len(auth_entity_or_entities_iterable) > 1:
            auth_entity_or_entities = auth_entity_or_entities_iterable
        else:
            auth_entity_or_entities = auth_entity_or_entities_iterable[0]

        all_perms = ["contenttypes.add_contenttype", "contenttypes.change_contenttype",
                     "contenttypes.delete_contenttype"]
        bulk_assign_perms(all_perms, auth_entity_or_entities)
        for auth_ent in auth_entity_or_entities_iterable:
            user = auth_entity_to_user[auth_ent]
            for perm in all_perms:
                self.assertTrue(
                    user.has_perm(perm)
                )

        # we store this variable to test both cases, an iterable and a single object argument
        if multiple_perms:
            perms = all_perms
        else:
            perms = "contenttypes.change_contenttype"

        self.clear_users_perms_caches(auth_entity_to_user.values())
        bulk_remove_perms(perms, auth_entity_or_entities)
        for auth_ent in auth_entity_or_entities_iterable:
            user = auth_entity_to_user[auth_ent]
            for perm in perms if isinstance(perms, (list, QuerySet)) else [perms]:
                self.assertFalse(
                    user.has_perm(perm)
                )

    def test_remove_single_global_perm_from_single_user(self):
        self._test_bulk_remove_global_perms(False, False, "user")

    def test_remove_single_global_perm_from_multiple_users(self):
        self._test_bulk_remove_global_perms(False, True, "user")

    def test_remove_multiple_global_perms_from_single_user(self):
        self._test_bulk_remove_global_perms(True, False, "user")

    def test_remove_multiple_global_perm_from_multiple_users(self):
        self._test_bulk_remove_global_perms(True, True, "user")

    def test_remove_single_global_perm_from_single_group(self):
        self._test_bulk_remove_global_perms(False, False, "group")

    def test_remove_single_global_perm_from_multiple_groups(self):
        self._test_bulk_remove_global_perms(False, True, "group")

    def test_remove_multiple_global_perms_from_single_group(self):
        self._test_bulk_remove_global_perms(True, False, "group")

    def test_remove_multiple_global_perm_from_multiple_groups(self):
        self._test_bulk_remove_global_perms(True, True, "group")

    def test_no_commit(self):
        perms_to_remove = "change_contenttype"
        affected_auth_entities = [self.user]
        obj = [self.ctype, self.extra_objs[0]]
        unaffected_extra_objs = self.extra_objs[1:]

        auth_entity_or_entities, all_affected_auth_entities, obj_iterable, perms_iterable = self._setup_bulk_remove_test(
            perms_to_remove,
            affected_auth_entities,
            obj,
        )

        # Test bulk remove.
        removed_perms = bulk_remove_perms(perms_to_remove, auth_entity_or_entities, obj, commit=False)

        # still have perms
        self._check_auth_entities_perms_on_objs(
            all_affected_auth_entities,
            obj_iterable,
            perms_iterable,
            have_perms=True
        )

        removed_perms.delete()

        self._check_auth_entities_perms_on_objs(
            all_affected_auth_entities,
            obj_iterable,
            perms_iterable,
            have_perms=False
        )

        if unaffected_extra_objs:
            self._check_auth_entities_perms_on_objs(
                all_affected_auth_entities,
                unaffected_extra_objs,
                perms_iterable,
                have_perms=True
            )

    def _setup_bulk_remove_test(
            self,
            perms_to_remove,
            affected_auth_entities,
            obj,
    ):
        if len(affected_auth_entities) > 1:
            auth_entity_or_entities = affected_auth_entities.copy()
        else:
            auth_entity_or_entities = affected_auth_entities[0]

        all_affected_auth_entities = affected_auth_entities.copy()
        for auth_entity in affected_auth_entities:
            user, group = get_identity(auth_entity)
            if group:
                all_affected_auth_entities.extend(list(group.user_set.all()))

        obj_iterable = obj if isinstance(obj, (list, QuerySet)) else [obj]
        perms_iterable = perms_to_remove if isinstance(perms_to_remove, (list, QuerySet)) else [perms_to_remove]
        all_assigned_perms = ["add_contenttype", "change_contenttype", "delete_contenttype"]

        # set up test by assigning all perms to affected_auth_entities for everything
        # and sanity check that perms have indeed been correctly assigned
        bulk_assign_perms(all_assigned_perms, affected_auth_entities, self.all_objects)
        self._check_auth_entities_perms_on_objs(
            all_affected_auth_entities,
            self.all_objects,
            all_assigned_perms,
            have_perms=True
        )

        return (
            auth_entity_or_entities,
            all_affected_auth_entities,
            obj_iterable,
            perms_iterable
        )

    def _test_remove_object_perms(
            self,
            perms_to_remove,
            affected_auth_entities,
            obj,
            unaffected_extra_objs
    ):
        auth_entity_or_entities, all_affected_auth_entities, obj_iterable, perms_iterable = self._setup_bulk_remove_test(
            perms_to_remove,
            affected_auth_entities,
            obj,
        )

        # Test bulk remove.
        bulk_remove_perms(perms_to_remove, auth_entity_or_entities, obj)

        self._check_auth_entities_perms_on_objs(
            all_affected_auth_entities,
            obj_iterable,
            perms_iterable,
            have_perms=False
        )

        if unaffected_extra_objs:
            self._check_auth_entities_perms_on_objs(
                all_affected_auth_entities,
                unaffected_extra_objs,
                perms_iterable,
                have_perms=True
            )

    def test_remove_single_perm_from_single_user_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.user],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_single_perm_from_single_user_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.user],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_single_perm_from_single_user_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.user],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_single_perm_from_multiple_users_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_single_perm_from_multiple_users_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.user, self.user_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_single_perm_from_multiple_users_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_single_perm_from_single_group_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.group],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_single_perm_from_single_group_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.group],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_single_perm_from_single_group_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.group],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_single_perm_from_multiple_groups_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_single_perm_from_multiple_groups_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.group, self.group_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_single_perm_from_multiple_groups_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove="change_contenttype",
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_multiple_perms_from_single_user_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_multiple_perms_from_single_user_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_multiple_perms_from_single_user_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_multiple_perms_from_multiple_users_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_multiple_perms_from_multiple_users_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user, self.user_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_multiple_perms_from_multiple_users_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.user, self.user_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_multiple_perms_from_single_group_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_multiple_perms_from_single_group_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_multiple_perms_from_single_group_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_multiple_perms_from_multiple_groups_for_single_obj(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype,
            unaffected_extra_objs=self.extra_objs,
        )

    def test_remove_multiple_perms_from_multiple_groups_for_list(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group, self.group_2],
            obj=[self.ctype, self.extra_objs[0]],
            unaffected_extra_objs=self.extra_objs[1:],
        )

    def test_remove_multiple_perms_from_multiple_groups_for_queryset(self):
        self._test_remove_object_perms(
            perms_to_remove=["add_contenttype", "change_contenttype"],
            affected_auth_entities=[self.group, self.group_2],
            obj=self.ctype_qset,
            unaffected_extra_objs=[],
        )

    def test_remove_perms_for_model_with_binary_field(self):
        model_with_binary_field = ModelWithBinaryField.objects.create()
        auth_entities = [self.group, self.group_2]
        perms_iterable = ["add_modelwithbinaryfield", "change_modelwithbinaryfield"]
        bulk_assign_perms(perms_iterable, auth_entities, [model_with_binary_field])
        self._check_auth_entities_perms_on_objs(
            auth_entities,
            [model_with_binary_field],
            perms_iterable,
            have_perms=True
        )

        bulk_remove_perms(
            perms_iterable,
            auth_entities,
            [model_with_binary_field]
        )

        # check that perms on post have been removed
        self._check_auth_entities_perms_on_objs(
            auth_entities,
            [model_with_binary_field],
            perms_iterable,
            have_perms=False
        )


    def test_remove_when_multiple_models_with_same_perm(self):
        """
        The reason this is tested is because there was a bug in this case.
        The scenario is that we have a permission with a certain name (here "add_post") that exists on two models in
        the same app.
        """
        assert ContentType.objects.get(model="post")
        project_ctype = ContentType.objects.get(model="project")
        Permission.objects.create(
            codename='add_post',
            name='Can add post',
            content_type=project_ctype
        )
        post = Post.objects.create(title='Post1')
        project = Project.objects.create(name='Project1')
        auth_entities = [self.group, self.group_2]
        perms_iterable = ["add_post"]

        # assign the same-named perm to both objects, and check the auth_entities have that perm on those objects
        bulk_assign_perms(perms_iterable, auth_entities, [post])
        bulk_assign_perms(perms_iterable, auth_entities, [project])
        for obj in [post, project]:
            self._check_auth_entities_perms_on_objs(
                auth_entities,
                [obj],
                perms_iterable,
                have_perms=True
            )

        bulk_remove_perms(
            perms_iterable,
            auth_entities,
            [post]
        )

        # check that perms on post have been removed, but not on project

        self._check_auth_entities_perms_on_objs(
            auth_entities,
            [post],
            perms_iterable,
            have_perms=False
        )

        self._check_auth_entities_perms_on_objs(
            auth_entities,
            [project],
            perms_iterable,
            have_perms=True
        )


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
                          perm="change_site",  # for global permissions must provide app_label
                          user_or_group=self.user)

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
            assign_perm("change_contenttype", self.user, self.ctype)

        perms = get_perms(self.user, self.ctype)
        for perm in perms_to_assign:
            self.assertTrue(perm in perms)


class GetUsersWithPermsTest(TestCase):
    """
    Tests get_users_with_perms function.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(
            model='bar', app_label='guardian-tests')
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
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1)
        result_vals = result.values_list('username', flat=True)

        self.assertEqual(
            set(result_vals),
            {user.username for user in (self.user1, self.user2)},
        )

    def test_only_with_perms_in(self):
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1, only_with_perms_in=('change_contenttype',))
        result_vals = result.values_list('username', flat=True)

        self.assertEqual(
            set(result_vals),
            {self.user1.username},
        )

    def test_only_with_perms_in_and_with_group_users(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)

        # assign perms to groups
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("add_contenttype", self.group3, self.obj2)

        result = get_users_with_perms(self.obj1, only_with_perms_in=('change_contenttype', 'delete_contenttype'),
                                      with_group_users=True)
        result_vals = result.values_list('username', flat=True)

        self.assertEqual(
            set(result_vals),
            {self.user1.username, self.user2.username},
        )

    def test_only_with_perms_in_and_not_with_group_users(self):
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)
        self.user3.groups.add(self.group3)

        # assign perms to groups
        assign_perm("change_contenttype", self.group1, self.obj1)
        assign_perm("delete_contenttype", self.group2, self.obj1)
        assign_perm("delete_contenttype", self.group3, self.obj2)

        # assign perms to user
        assign_perm("change_contenttype", self.user2, self.obj1)

        result = get_users_with_perms(self.obj1, only_with_perms_in=('change_contenttype', 'delete_contenttype'),
                                      with_group_users=False)
        result_vals = result.values_list('username', flat=True)

        self.assertEqual(
            set(result_vals),
            {self.user2.username},
        )

    def test_only_with_perms_in_attached(self):
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("change_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user2, self.obj1)
        assign_perm("delete_contenttype", self.user3, self.obj2)

        result = get_users_with_perms(self.obj1, only_with_perms_in=('delete_contenttype',),
                                      attach_perms=True)

        expected = {self.user2: ('change_contenttype', 'delete_contenttype')}
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

        result = get_users_with_perms(self.obj1).values_list('pk',
                                                             flat=True)
        self.assertEqual(
            set(result),
            {u.pk for u in (self.user1, self.user2)}
        )

    def test_users_groups_after_removal(self):
        self.test_users_groups_perms()
        remove_perm("change_contenttype", self.group1, self.obj1)

        result = get_users_with_perms(self.obj1).values_list('pk',
                                                             flat=True)
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
        admin = User.objects.create(username='admin', is_superuser=True)
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
        result = get_users_with_perms(self.obj1, with_group_users=False,
                                      attach_perms=True)
        expected = {self.user2: ["change_contenttype"]}
        self.assertEqual(result, expected)

    def test_direct_perms_only(self):
        admin = User.objects.create(username='admin', is_superuser=True)
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group1)
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", admin, self.obj1)
        assign_perm("delete_contenttype", self.group1, self.obj1)
        expected = {self.user1, self.user2, admin}
        result = get_users_with_perms(self.obj1, with_superusers=False, with_group_users=True)
        self.assertEqual(set(result), expected)
        self.assertEqual(set(get_user_perms(self.user1, self.obj1)), {'change_contenttype'})
        self.assertEqual(set(get_user_perms(self.user2, self.obj1)), set())
        self.assertEqual(set(get_user_perms(admin, self.obj1)), {'delete_contenttype'})
        result = get_users_with_perms(self.obj1, with_superusers=False, with_group_users=False)
        expected = {self.user1, admin}
        self.assertEqual(set(result), expected)
        self.assertEqual(set(get_group_perms(self.user1, self.obj1)), {'delete_contenttype'})
        self.assertEqual(set(get_group_perms(self.user2, self.obj1)), {'delete_contenttype'})
        self.assertEqual(set(get_group_perms(self.group1, self.obj1)), {'delete_contenttype'})
        self.assertEqual(set(get_group_perms(self.group2, self.obj1)), set())
        self.assertEqual(set(get_group_perms(admin, self.obj1)), set())
        expected_permissions = ['add_contenttype', 'change_contenttype', 'delete_contenttype']
        if django.VERSION >= (2, 1):
            expected_permissions.append('view_contenttype')
        self.assertEqual(set(get_perms(admin, self.obj1)), set(expected_permissions))
        self.assertEqual(set(get_perms(self.user1, self.obj1)), {'change_contenttype', 'delete_contenttype'})
        self.assertEqual(set(get_perms(self.user2, self.obj1)), {'delete_contenttype'})
        self.assertEqual(set(get_perms(self.group1, self.obj1)), {'delete_contenttype'})
        self.assertEqual(set(get_perms(self.group2, self.obj1)), set())

    def test_direct_perms_only_perms_attached(self):
        admin = User.objects.create(username='admin', is_superuser=True)
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group1)
        assign_perm("change_contenttype", self.user1, self.obj1)
        assign_perm("delete_contenttype", admin, self.obj1)
        assign_perm("delete_contenttype", self.group1, self.obj1)
        expected = {
            self.user1: ["change_contenttype", "delete_contenttype"],
            admin: ["add_contenttype", "change_contenttype", "delete_contenttype"],
            self.user2: ["delete_contenttype"]
        }
        if django.VERSION >= (2, 1):
            expected[admin].append("view_contenttype")
        result = get_users_with_perms(self.obj1, attach_perms=True,
                                      with_superusers=False, with_group_users=True)
        self.assertEqual(result.keys(), expected.keys())
        for key, perms in result.items():
            self.assertEqual(set(perms), set(expected[key]))
        result = get_users_with_perms(self.obj1, attach_perms=True,
                                      with_superusers=False, with_group_users=False)
        expected = {self.user1: ["change_contenttype"],
                    admin: ["delete_contenttype"]}
        self.assertEqual(result, expected)

    def test_without_group_users_no_result(self):
        self.user1.groups.add(self.group1)
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_users_with_perms(self.obj1, attach_perms=True,
                                      with_group_users=False)
        expected = {}
        self.assertEqual(result, expected)

    def test_without_group_users_no_result_but_with_superusers(self):
        admin = User.objects.create(username='admin', is_superuser=True)
        self.user1.groups.add(self.group1)
        assign_perm("change_contenttype", self.group1, self.obj1)
        result = get_users_with_perms(self.obj1, with_group_users=False,
                                      with_superusers=True)
        expected = [admin]
        self.assertEqual(set(result), set(expected))


class GetGroupsWithPerms(TestCase):
    """
    Tests get_groups_with_perms function.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(
            model='bar', app_label='guardian-tests')
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
        obj = ContentType.objects.create(pk=1042, model='baz', app_label='guardian-tests')
        group = Group.objects.create(pk=1042, name='group')

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


class GetObjectsForUser(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='joe')
        self.group = Group.objects.create(name='group')
        self.ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')

    def test_superuser(self):
        self.user.is_superuser = True
        ctypes = ContentType.objects.all()
        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'], ctypes)
        self.assertEqual(set(ctypes), set(objects))

    def test_with_superuser_true(self):
        self.user.is_superuser = True
        ctypes = ContentType.objects.all()
        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'], ctypes, with_superuser=True)
        self.assertEqual(set(ctypes), set(objects))

    def test_with_superuser_false(self):
        self.user.is_superuser = True
        ctypes = ContentType.objects.all()
        obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        assign_perm('change_contenttype', self.user, obj1)
        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'], ctypes, with_superuser=False)
        self.assertEqual({obj1}, set(objects))

    def test_anonymous(self):
        self.user = AnonymousUser()
        ctypes = ContentType.objects.all()
        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'], ctypes)

        obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        assign_perm('change_contenttype', self.user, obj1)
        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'], ctypes)
        self.assertEqual({obj1}, set(objects))

    def test_mixed_perms(self):
        codenames = [
            get_user_permission_full_codename('change'),
            'auth.change_permission',
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_user,
                          self.user, codenames)

    def test_perms_with_mixed_apps(self):
        codenames = [
            get_user_permission_full_codename('change'),
            'contenttypes.change_contenttype',
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_user,
                          self.user, codenames)

    def test_mixed_perms_and_klass(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_user,
                          self.user, ['auth.change_group'], User)

    def test_no_app_label_nor_klass(self):
        self.assertRaises(WrongAppError, get_objects_for_user, self.user,
                          ['change_group'])

    def test_empty_perms_sequence(self):
        objects = get_objects_for_user(self.user, [], Group.objects.all())
        self.assertEqual(
            set(objects),
            set()
        )

    def test_perms_single(self):
        perm = 'auth.change_group'
        assign_perm(perm, self.user, self.group)
        self.assertEqual(
            set(get_objects_for_user(self.user, perm)),
            set(get_objects_for_user(self.user, [perm])))

    def test_klass_as_model(self):
        assign_perm('contenttypes.change_contenttype', self.user, self.ctype)

        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'], ContentType)
        self.assertEqual([obj.name for obj in objects], [self.ctype.name])

    def test_klass_as_manager(self):
        assign_perm('auth.change_group', self.user, self.group)
        objects = get_objects_for_user(self.user, ['auth.change_group'],
                                       Group.objects)
        self.assertEqual([obj.name for obj in objects], [self.group.name])

    def test_klass_as_queryset(self):
        assign_perm('auth.change_group', self.user, self.group)
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
            assign_perm('change_group', self.user, group)

        objects = get_objects_for_user(self.user, ['auth.change_group'])
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects),
            set(groups))

    def test_multiple_perms_to_check(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm('auth.change_group', self.user, group)
        assign_perm('auth.delete_group', self.user, groups[1])

        objects = get_objects_for_user(self.user, ['auth.change_group',
                                                   'auth.delete_group'])
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('name', flat=True)),
            {groups[1].name})

    def test_multiple_perms_to_check_no_groups(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm('auth.change_group', self.user, group)
        assign_perm('auth.delete_group', self.user, groups[1])

        objects = get_objects_for_user(self.user, ['auth.change_group',
                                                   'auth.delete_group'], use_groups=False)
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('name', flat=True)),
            {groups[1].name})

    def test_any_of_multiple_perms_to_check(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        assign_perm('auth.change_group', self.user, groups[0])
        assign_perm('auth.delete_group', self.user, groups[2])

        objects = get_objects_for_user(self.user, ['auth.change_group',
                                                   'auth.delete_group'], any_perm=True)
        self.assertEqual(len(objects), 2)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('name', flat=True)),
            {groups[0].name, groups[2].name})

    def test_groups_perms(self):
        group1 = Group.objects.create(name='group1')
        group2 = Group.objects.create(name='group2')
        group3 = Group.objects.create(name='group3')
        groups = [group1, group2, group3]
        for group in groups:
            self.user.groups.add(group)

        # Objects to operate on
        ctypes = list(ContentType.objects.all().order_by('id'))
        assign_perm('auth.change_group', self.user)
        assign_perm('change_contenttype', self.user, ctypes[0])
        assign_perm('change_contenttype', self.user, ctypes[1])
        assign_perm('delete_contenttype', self.user, ctypes[1])
        assign_perm('delete_contenttype', self.user, ctypes[2])

        assign_perm('change_contenttype', groups[0], ctypes[3])
        assign_perm('change_contenttype', groups[1], ctypes[3])
        assign_perm('change_contenttype', groups[2], ctypes[4])
        assign_perm('delete_contenttype', groups[0], ctypes[0])

        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'])
        self.assertEqual(
            set(objects.values_list('id', flat=True)),
            {ctypes[i].id for i in [0, 1, 3, 4]})

        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype',
                                        'contenttypes.delete_contenttype'])
        self.assertEqual(
            set(objects.values_list('id', flat=True)),
            {ctypes[i].id for i in [0, 1]})

        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype'])
        self.assertEqual(
            set(objects.values_list('id', flat=True)),
            {ctypes[i].id for i in [0, 1, 3, 4]})

    def test_has_global_permission_only(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to change any group
        perm = 'auth.change_group'

        assign_perm(perm, self.user)
        objects = get_objects_for_user(self.user, perm)
        remove_perm(perm, self.user)
        self.assertEqual(set(objects),
                         set(Group.objects.all()))

    def test_has_global_permission_and_object_based_permission(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to change any group
        perm_global = 'auth.change_group'
        perm_obj = 'delete_group'
        assign_perm(perm_global, self.user)
        assign_perm(perm_obj, self.user, groups[0])
        objects = get_objects_for_user(self.user, [perm_global, perm_obj])
        remove_perm(perm_global, self.user)
        self.assertEqual(set(objects.values_list('name', flat=True)),
                         {groups[0].name})

    def test_has_global_permission_and_object_based_permission_any_perm(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to change any group
        perm_global = 'auth.change_group'
        # object based permission to change only a specific group
        perm_obj = 'auth.delete_group'
        assign_perm(perm_global, self.user)
        assign_perm(perm_obj, self.user, groups[0])
        objects = get_objects_for_user(
            self.user, [perm_global, perm_obj], any_perm=True, accept_global_perms=True)
        remove_perm(perm_global, self.user)
        self.assertEqual(set(objects),
                         set(Group.objects.all()))

    def test_object_based_permission_without_global_permission(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        # global permission to delete any group
        perm_global = 'auth.delete_group'
        perm_obj = 'auth.delete_group'
        assign_perm(perm_global, self.user)
        assign_perm(perm_obj, self.user, groups[0])
        objects = get_objects_for_user(
            self.user, [perm_obj], accept_global_perms=False)
        remove_perm(perm_global, self.user)
        self.assertEqual(set(objects.values_list('name', flat=True)),
                         {groups[0].name})

    def test_object_based_permission_with_groups_2perms(self):
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            self.user.groups.add(group)
        # Objects to operate on
        ctypes = list(ContentType.objects.all().order_by('id'))
        assign_perm('contenttypes.change_contenttype', self.user)
        assign_perm('change_contenttype', self.user, ctypes[0])
        assign_perm('change_contenttype', self.user, ctypes[1])
        assign_perm('delete_contenttype', self.user, ctypes[1])
        assign_perm('delete_contenttype', self.user, ctypes[2])

        assign_perm('change_contenttype', groups[0], ctypes[3])
        assign_perm('change_contenttype', groups[1], ctypes[3])
        assign_perm('change_contenttype', groups[2], ctypes[4])
        assign_perm('delete_contenttype', groups[0], ctypes[0])

        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype',
                                        'contenttypes.delete_contenttype'], accept_global_perms=True)
        self.assertEqual(
            set(objects.values_list('id', flat=True)),
            {ctypes[0].id, ctypes[1].id, ctypes[2].id})

    def test_object_based_permission_with_groups_3perms(self):

        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            self.user.groups.add(group)
        # Objects to operate on
        ctypes = list(ContentType.objects.all().order_by('id'))
        assign_perm('contenttypes.change_contenttype', self.user)
        assign_perm('change_contenttype', self.user, ctypes[0])
        assign_perm('change_contenttype', self.user, ctypes[1])
        assign_perm('delete_contenttype', self.user, ctypes[1])
        assign_perm('delete_contenttype', self.user, ctypes[2])
        # add_contenttype does not make sense, here just for testing purposes,
        # to also cover one if branch in function.
        assign_perm('add_contenttype', self.user, ctypes[1])

        assign_perm('change_contenttype', groups[0], ctypes[3])
        assign_perm('change_contenttype', groups[1], ctypes[3])
        assign_perm('change_contenttype', groups[2], ctypes[4])
        assign_perm('delete_contenttype', groups[0], ctypes[0])
        assign_perm('add_contenttype', groups[0], ctypes[0])

        objects = get_objects_for_user(self.user,
                                       ['contenttypes.change_contenttype',
                                        'contenttypes.delete_contenttype', 'contenttypes.add_contenttype'],
                                       accept_global_perms=True)
        self.assertEqual(
            set(objects.values_list('id', flat=True)),
            {ctypes[0].id, ctypes[1].id})

    def test_varchar_primary_key(self):
        """
        Verify that the function works when the objects that should be returned
        have varchar primary keys.
        """
        obj_with_char_pk = CharPKModel.objects.create(
            char_pk='testprimarykey')
        assign_perm('add_charpkmodel', self.user, obj_with_char_pk)

        objects = get_objects_for_user(self.user, 'testapp.add_charpkmodel')
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('pk', flat=True)),
            {obj_with_char_pk.pk})

    def test_uuid_primary_key(self):
        """
        Verify that the function works when the objects that should be returned
        have uuid primary keys.
        """
        obj_with_uuid_pk = UUIDPKModel.objects.create()
        assign_perm('add_uuidpkmodel', self.user, obj_with_uuid_pk)

        objects = get_objects_for_user(self.user, 'testapp.add_uuidpkmodel')
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('pk', flat=True)),
            {obj_with_uuid_pk.pk})

    def test_varchar_primary_key_with_any_perm(self):
        """
        Verify that the function works with any_perm set to True when the
        objects that should be returned have varchar primary keys.
        """
        obj_with_char_pk = CharPKModel.objects.create(
            char_pk='testprimarykey')
        assign_perm('add_charpkmodel', self.user, obj_with_char_pk)

        objects = get_objects_for_user(
            self.user,
            ['testapp.add_charpkmodel', 'testapp.change_charpkmodel'],
            any_perm=True)
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('pk', flat=True)),
            {obj_with_char_pk.pk})

    def test_uuid_primary_key_with_any_perm(self):
        """
        Verify that the function works with any_perm set to True when the
        objects that should be returned have uuid primary keys.
        """
        obj_with_uuid_pk = UUIDPKModel.objects.create()
        assign_perm('add_uuidpkmodel', self.user, obj_with_uuid_pk)

        objects = get_objects_for_user(
            self.user,
            ['testapp.add_uuidpkmodel', 'testapp.change_uuidpkmodel'],
            any_perm=True)
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('pk', flat=True)),
            {obj_with_uuid_pk.pk})

    def test_varchar_primary_key_with_group_values(self):
        """
        Verify that the function works when the objects that should be returned
        have varchar primary keys, and those objects are due to the user's
        groups.
        """
        obj_with_char_pk = CharPKModel.objects.create(
            char_pk='testprimarykey')
        assign_perm('add_charpkmodel', self.group, obj_with_char_pk)
        self.user.groups.add(self.group)

        objects = get_objects_for_user(
            self.user,
            ['testapp.add_charpkmodel', 'testapp.change_charpkmodel'],
            any_perm=True)
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('pk', flat=True)),
            {obj_with_char_pk.pk})

    def test_model_inheritance(self):
        child_with_perm = ChildTestModel.objects.create(name="child1")
        assign_perm('testapp.change_childtestmodel', self.user, child_with_perm)
        child_without_perm = ChildTestModel.objects.create(name="child2")

        children = get_objects_for_user(self.user, 'testapp.change_childtestmodel', ChildTestModel)

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
        assign_perm('add_uuidpkmodel', self.group, obj_with_uuid_pk)
        self.user.groups.add(self.group)

        objects = get_objects_for_user(
            self.user,
            ['testapp.add_uuidpkmodel', 'testapp.change_uuidpkmodel'],
            any_perm=True)
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects.values_list('pk', flat=True)),
            {obj_with_uuid_pk.pk})

    def test_exception_different_ctypes(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_user,
                          self.user, ['auth.change_permission', 'auth.change_group'])

    def test_has_any_permissions(self):
        # We use groups as objects.
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm('change_group', self.user, group)

        objects = get_objects_for_user(self.user, [], Group)
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects),
            set(groups))

    def test_short_codenames_with_klass(self):
        assign_perm('contenttypes.change_contenttype', self.user, self.ctype)

        objects = get_objects_for_user(self.user,
                                       ['change_contenttype'], ContentType)
        self.assertEqual([obj.name for obj in objects], [self.ctype.name])

    def test_has_any_group_permissions(self):
        # We use groups as objects.
        group_names = ['group1', 'group2', 'group3']
        groups = [Group.objects.create(name=name) for name in group_names]
        for group in groups:
            assign_perm('change_group', self.group, group)

        objects = get_objects_for_group(self.group, [], Group)
        self.assertEqual(len(objects), len(groups))
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects),
            set(groups))


class GetObjectsForGroup(TestCase):
    """
    Tests get_objects_for_group function.
    """

    def setUp(self):
        self.obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(
            model='bar', app_label='guardian-tests')
        self.obj3 = ContentType.objects.create(
            model='baz', app_label='guardian-tests')
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        self.group1 = Group.objects.create(name='group1')
        self.group2 = Group.objects.create(name='group2')
        self.group3 = Group.objects.create(name='group3')

    def test_mixed_perms(self):
        codenames = [
            get_user_permission_full_codename('change'),
            'auth.change_permission',
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_group,
                          self.group1, codenames)

    def test_perms_with_mixed_apps(self):
        codenames = [
            get_user_permission_full_codename('change'),
            'contenttypes.contenttypes.change_contenttype',
        ]
        self.assertRaises(MixedContentTypeError, get_objects_for_group,
                          self.group1, codenames)

    def test_mixed_perms_and_klass(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_group,
                          self.group1, ['auth.change_group'], User)

    def test_no_app_label_nor_klass(self):
        self.assertRaises(WrongAppError, get_objects_for_group, self.group1,
                          ['change_contenttype'])

    def test_empty_perms_sequence(self):
        self.assertEqual(
            set(get_objects_for_group(self.group1, [], ContentType)),
            set()
        )

    def test_perms_single(self):
        perm = 'contenttypes.change_contenttype'
        assign_perm(perm, self.group1, self.obj1)
        self.assertEqual(
            set(get_objects_for_group(self.group1, perm)),
            set(get_objects_for_group(self.group1, [perm]))
        )

    def test_klass_as_model(self):
        assign_perm('contenttypes.change_contenttype', self.group1, self.obj1)

        objects = get_objects_for_group(self.group1,
                                        ['contenttypes.change_contenttype'], ContentType)
        self.assertEqual([obj.name for obj in objects], [self.obj1.name])

    def test_klass_as_manager(self):
        assign_perm('contenttypes.change_contenttype', self.group1, self.obj1)
        objects = get_objects_for_group(self.group1, ['change_contenttype'],
                                        ContentType.objects)
        self.assertEqual(list(objects), [self.obj1])

    def test_klass_as_queryset(self):
        assign_perm('contenttypes.change_contenttype', self.group1, self.obj1)
        objects = get_objects_for_group(self.group1, ['change_contenttype'],
                                        ContentType.objects.all())
        self.assertEqual(list(objects), [self.obj1])

    def test_ensure_returns_queryset(self):
        objects = get_objects_for_group(
            self.group1, ['contenttypes.change_contenttype'])
        self.assertTrue(isinstance(objects, QuerySet))

    def test_simple(self):
        assign_perm('change_contenttype', self.group1, self.obj1)
        assign_perm('change_contenttype', self.group1, self.obj2)

        objects = get_objects_for_group(
            self.group1, 'contenttypes.change_contenttype')
        self.assertEqual(len(objects), 2)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(
            set(objects),
            {self.obj1, self.obj2})

    def test_simple_after_removal(self):
        self.test_simple()
        remove_perm('change_contenttype', self.group1, self.obj1)
        objects = get_objects_for_group(
            self.group1, 'contenttypes.change_contenttype')
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.obj2)

    def test_multiple_perms_to_check(self):
        assign_perm('change_contenttype', self.group1, self.obj1)
        assign_perm('delete_contenttype', self.group1, self.obj1)
        assign_perm('change_contenttype', self.group1, self.obj2)

        objects = get_objects_for_group(self.group1, [
            'contenttypes.change_contenttype',
            'contenttypes.delete_contenttype'])
        self.assertEqual(len(objects), 1)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual(objects[0], self.obj1)

    def test_any_of_multiple_perms_to_check(self):
        assign_perm('change_contenttype', self.group1, self.obj1)
        assign_perm('delete_contenttype', self.group1, self.obj1)
        assign_perm('add_contenttype', self.group1, self.obj2)
        assign_perm('delete_contenttype', self.group1, self.obj3)

        objects = get_objects_for_group(self.group1,
                                        ['contenttypes.change_contenttype',
                                         'contenttypes.delete_contenttype'], any_perm=True)
        self.assertTrue(isinstance(objects, QuerySet))
        self.assertEqual([obj for obj in objects.order_by('app_label', 'id')],
                         [self.obj1, self.obj3])

    def test_results_for_different_groups_are_correct(self):
        assign_perm('change_contenttype', self.group1, self.obj1)
        assign_perm('delete_contenttype', self.group2, self.obj2)

        self.assertEqual(set(get_objects_for_group(self.group1, 'contenttypes.change_contenttype')),
                         {self.obj1})
        self.assertEqual(set(get_objects_for_group(self.group2, 'contenttypes.change_contenttype')),
                         set())
        self.assertEqual(set(get_objects_for_group(self.group2, 'contenttypes.delete_contenttype')),
                         {self.obj2})

    def test_has_global_permission(self):
        assign_perm('contenttypes.change_contenttype', self.group1)

        objects = get_objects_for_group(
            self.group1, ['contenttypes.change_contenttype'])
        self.assertEqual(set(objects),
                         set(ContentType.objects.all()))

    def test_has_global_permission_and_object_based_permission(self):
        assign_perm('contenttypes.change_contenttype', self.group1)
        assign_perm('contenttypes.delete_contenttype', self.group1, self.obj1)

        objects = get_objects_for_group(self.group1, [
            'contenttypes.change_contenttype', 'contenttypes.delete_contenttype'], any_perm=False)
        self.assertEqual(set(objects),
                         {self.obj1})

    def test_has_global_permission_and_object_based_permission_any_perm(self):
        assign_perm('contenttypes.change_contenttype', self.group1)
        assign_perm('contenttypes.delete_contenttype', self.group1, self.obj1)

        objects = get_objects_for_group(self.group1, [
            'contenttypes.change_contenttype', 'contenttypes.delete_contenttype'], any_perm=True)
        self.assertEqual(set(objects),
                         set(ContentType.objects.all()))

    def test_has_global_permission_and_object_based_permission_3perms(self):
        assign_perm('contenttypes.change_contenttype', self.group1)
        assign_perm('contenttypes.delete_contenttype', self.group1, self.obj1)
        assign_perm('contenttypes.add_contenttype', self.group1, self.obj2)

        objects = get_objects_for_group(self.group1, [
            'contenttypes.change_contenttype', 'contenttypes.delete_contenttype', 'contenttypes.add_contenttype'],
                                        any_perm=False)
        self.assertEqual(set(objects),
                         set())

    def test_exception_different_ctypes(self):
        self.assertRaises(MixedContentTypeError, get_objects_for_group,
                          self.group1, ['auth.change_permission', 'auth.change_group'])
