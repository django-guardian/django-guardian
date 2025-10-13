import copy
import os
import unittest

from django import VERSION as DJANGO_VERSION
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from guardian.admin import GuardedInlineAdminMixin, GuardedModelAdmin
from guardian.models import Group
from guardian.shortcuts import assign_perm, get_perms, get_perms_for_model, remove_perm
from guardian.testapp.models import LogEntryWithGroup as LogEntry
from guardian.testapp.models import UserProfile
from guardian.testapp.tests.conf import skipUnlessTestApp

User = get_user_model()


# Test inline admin class using GuardedInlineAdminMixin
class UserProfileInline(GuardedInlineAdminMixin, admin.StackedInline):
    """Test inline for UserProfile model using GuardedInlineAdminMixin."""

    model = UserProfile
    extra = 0


# Test admin class with inline
class UserAdminWithProfile(GuardedModelAdmin):
    """Test admin for User model with inline forms."""

    inlines = [UserProfileInline]


class ContentTypeGuardedAdmin(GuardedModelAdmin):
    pass


try:
    admin.site.unregister(ContentType)
except admin.sites.NotRegistered:
    pass
admin.site.register(ContentType, ContentTypeGuardedAdmin)


class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "admin")
        self.user = User.objects.create_user("joe", "joe@example.com", "joe")
        self.group = Group.objects.create(name="group")
        self.client = Client()
        self.obj = ContentType.objects.create(model="bar", app_label="fake-for-guardian-tests")
        self.obj_info = self.obj._meta.app_label, self.obj._meta.model_name

    def tearDown(self):
        self.client.logout()

    def _login_superuser(self):
        self.client.login(username="admin", password="admin")

    def test_view_manage_wrong_obj(self):
        self._login_superuser()
        url = reverse(
            "admin:%s_%s_permissions_manage_user" % self.obj_info, kwargs={"object_pk": -10, "user_id": self.user.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["object"], self.obj)

    def test_view_manage_wrong_user(self):
        self._login_superuser()
        url = reverse(
            "admin:%s_%s_permissions_manage_user" % self.obj_info, kwargs={"object_pk": self.obj.pk, "user_id": -10}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view_manage_user_form(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"user": self.user.username, "submit_manage_user": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse(
            "admin:%s_%s_permissions_manage_user" % self.obj_info,
            kwargs={"object_pk": self.obj.pk, "user_id": self.user.pk},
        )
        self.assertEqual(response.request["PATH_INFO"], redirect_url)

    @unittest.skipIf(
        DJANGO_VERSION >= (3, 0) and "mysql" in os.environ.get("DATABASE_URL", ""),
        "Negative ids no longer work in Django 3.0+ with MySQL.",
    )
    def test_view_manage_negative_user_form(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        self.user = User.objects.create(username="negative_id_user", pk=-2010)
        data = {"user": self.user.username, "submit_manage_user": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse("admin:%s_%s_permissions_manage_user" % self.obj_info, args=[self.obj.pk, self.user.pk])
        self.assertEqual(response.request["PATH_INFO"], redirect_url)

    def test_view_manage_user_form_wrong_user(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"user": "wrong-user", "submit_manage_user": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("user" in response.context["user_form"].errors)

    def test_view_manage_user_form_wrong_field(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"user": "<xss>", "submit_manage_user": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("user" in response.context["user_form"].errors)

    def test_view_manage_user_form_empty_user(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"user": "", "submit_manage_user": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("user" in response.context["user_form"].errors)

    def test_view_manage_user_wrong_perms(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions_manage_user" % self.obj_info, args=[self.obj.pk, self.user.pk])
        perms = ["change_user"]  # This is not self.obj related permission
        data = {"permissions": perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("permissions" in response.context["form"].errors)

    def test_view_manage_user(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions_manage_user" % self.obj_info, args=[self.obj.pk, self.user.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = {c[0] for c in response.context["form"].fields["permissions"].choices}
        self.assertEqual(
            {p.codename for p in get_perms_for_model(self.obj)},
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ["change_%s" % self.obj_info[1], "delete_%s" % self.obj_info[1]]
        data = {"permissions": perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertIn("selected", str(response.context["form"]))
        self.assertEqual(
            set(get_perms(self.user, self.obj)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ["change_%s" % self.obj_info[1]]
        data = {"permissions": perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.user, self.obj)),
            set(perms),
        )

    def test_view_manage_group_form(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"group": self.group.name, "submit_manage_group": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse(
            "admin:%s_%s_permissions_manage_group" % self.obj_info, args=[self.obj.pk, self.group.id]
        )
        self.assertEqual(response.request["PATH_INFO"], redirect_url)

    @unittest.skipIf(
        DJANGO_VERSION >= (3, 0) and "mysql" in os.environ.get("DATABASE_URL", ""),
        "Negative ids no longer work in Django 3.0+ with MySQL.",
    )
    def test_view_manage_negative_group_form(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        self.group = Group.objects.create(name="neagive_id_group", id=-2010)
        data = {"group": self.group.name, "submit_manage_group": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse(
            "admin:%s_%s_permissions_manage_group" % self.obj_info, args=[self.obj.pk, self.group.id]
        )
        self.assertEqual(response.request["PATH_INFO"], redirect_url)

    def test_view_manage_group_form_wrong_group(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"group": "wrong-group", "submit_manage_group": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("group" in response.context["group_form"].errors)

    def test_view_manage_group_form_wrong_field(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"group": "<xss>", "submit_manage_group": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("group" in response.context["group_form"].errors)

    def test_view_manage_group_form_empty_group(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions" % self.obj_info, args=[self.obj.pk])
        data = {"group": "", "submit_manage_group": "submit"}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("group" in response.context["group_form"].errors)

    def test_view_manage_group_wrong_perms(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions_manage_group" % self.obj_info, args=[self.obj.pk, self.group.id])
        perms = ["change_user"]  # This is not self.obj related permission
        data = {"permissions": perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("permissions" in response.context["form"].errors)

    def test_view_manage_group(self):
        self._login_superuser()
        url = reverse("admin:%s_%s_permissions_manage_group" % self.obj_info, args=[self.obj.pk, self.group.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = {c[0] for c in response.context["form"].fields["permissions"].choices}
        self.assertEqual(
            {p.codename for p in get_perms_for_model(self.obj)},
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ["change_%s" % self.obj_info[1], "delete_%s" % self.obj_info[1]]
        data = {"permissions": perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.obj)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ["delete_%s" % self.obj_info[1]]
        data = {"permissions": perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.obj)),
            set(perms),
        )


if "django.contrib.admin" not in settings.INSTALLED_APPS:
    # Skip admin tests if admin app is not registered
    # we simpy clean up AdminTests class ...
    # TODO: use @unittest.skipUnless('django.contrib.admin' in settings.INSTALLED_APPS)
    #       if possible (requires Python 2.7, though)
    AdminTests = type("AdminTests", (TestCase,), {})


@skipUnlessTestApp
class GuardedModelAdminTests(TestCase):
    def _get_gma(self, attrs=None, name=None, model=None):
        """
        Returns ``GuardedModelAdmin`` instance.
        """
        attrs = attrs or {}
        name = str(name or "GMA")
        model = model or User
        GMA = type(name, (GuardedModelAdmin,), attrs)
        gma = GMA(model, admin.site)
        return gma

    def test_obj_perms_manage_template_attr(self):
        attrs = {"obj_perms_manage_template": "foobar.html"}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_template(), "foobar.html")

    def test_obj_perms_manage_user_template_attr(self):
        attrs = {"obj_perms_manage_user_template": "foobar.html"}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_user_template(), "foobar.html")

    def test_obj_perms_manage_user_form_attr(self):
        attrs = {"obj_perms_manage_user_form": forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_manage_user_form(None), forms.Form))

    def test_obj_perms_user_select_form_attr(self):
        attrs = {"obj_perms_user_select_form": forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_user_select_form(None), forms.Form))

    def test_obj_perms_manage_group_template_attr(self):
        attrs = {"obj_perms_manage_group_template": "foobar.html"}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_group_template(), "foobar.html")

    def test_obj_perms_manage_group_form_attr(self):
        attrs = {"obj_perms_manage_group_form": forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_manage_group_form(None), forms.Form))

    def test_obj_perms_group_select_form_attr(self):
        attrs = {"obj_perms_group_select_form": forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_group_select_form(None), forms.Form))

    def test_user_can_acces_owned_objects_only(self):
        attrs = {
            "user_can_access_owned_objects_only": True,
            "user_owned_objects_field": "user",
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_user("joe", "joe@example.com", "joe")
        jane = User.objects.create_user("jane", "jane@example.com", "jane")
        ctype = ContentType.objects.get_for_model(User)
        joe_entry = LogEntry.objects.create(
            user=joe, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo"
        )
        LogEntry.objects.create(user=jane, content_type=ctype, object_id=jane.pk, action_flag=1, change_message="bar")
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual([e.pk for e in qs], [joe_entry.pk])

    def test_user_can_acces_owned_objects_only_unless_superuser(self):
        attrs = {
            "user_can_access_owned_objects_only": True,
            "user_owned_objects_field": "user",
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_superuser("joe", "joe@example.com", "joe")
        jane = User.objects.create_user("jane", "jane@example.com", "jane")
        ctype = ContentType.objects.get_for_model(User)
        joe_entry = LogEntry.objects.create(
            user=joe, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo"
        )
        jane_entry = LogEntry.objects.create(
            user=jane, content_type=ctype, object_id=jane.pk, action_flag=1, change_message="bar"
        )
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual(sorted(e.pk for e in qs), sorted([joe_entry.pk, jane_entry.pk]))

    def test_user_can_access_owned_by_group_objects_only(self):
        attrs = {
            "user_can_access_owned_by_group_objects_only": True,
            "group_owned_objects_field": "group",
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_user("joe", "joe@example.com", "joe")
        joe_group = Group.objects.create(name="joe-group")
        joe.groups.add(joe_group)
        jane = User.objects.create_user("jane", "jane@example.com", "jane")
        jane_group = Group.objects.create(name="jane-group")
        jane.groups.add(jane_group)
        ctype = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(user=joe, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo")
        LogEntry.objects.create(user=jane, content_type=ctype, object_id=jane.pk, action_flag=1, change_message="bar")
        joe_entry_group = LogEntry.objects.create(
            user=jane, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo", group=joe_group
        )
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual([e.pk for e in qs], [joe_entry_group.pk])

    def test_user_can_access_owned_by_group_objects_only_unless_superuser(self):
        attrs = {
            "user_can_access_owned_by_group_objects_only": True,
            "group_owned_objects_field": "group",
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_superuser("joe", "joe@example.com", "joe")
        joe_group = Group.objects.create(name="joe-group")
        joe.groups.add(joe_group)
        jane = User.objects.create_user("jane", "jane@example.com", "jane")
        jane_group = Group.objects.create(name="jane-group")
        jane.groups.add(jane_group)
        ctype = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(user=joe, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo")
        LogEntry.objects.create(user=jane, content_type=ctype, object_id=jane.pk, action_flag=1, change_message="bar")
        LogEntry.objects.create(
            user=jane, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo", group=joe_group
        )
        LogEntry.objects.create(
            user=joe, content_type=ctype, object_id=joe.pk, action_flag=1, change_message="foo", group=jane_group
        )
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual(sorted(e.pk for e in qs), sorted(LogEntry.objects.values_list("pk", flat=True)))


class GrappelliGuardedModelAdminTests(TestCase):
    org_installed_apps = copy.copy(settings.INSTALLED_APPS)

    def _get_gma(self, attrs=None, name=None, model=None):
        """
        Returns ``GuardedModelAdmin`` instance.
        """
        attrs = attrs or {}
        name = str(name or "GMA")
        model = model or User
        GMA = type(name, (GuardedModelAdmin,), attrs)
        gma = GMA(model, admin.site)
        return gma

    def setUp(self):
        settings.INSTALLED_APPS = ["grappelli"] + list(settings.INSTALLED_APPS)

    def tearDown(self):
        settings.INSTALLED_APPS = self.org_installed_apps

    def test_get_obj_perms_manage_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_template(), "admin/guardian/contrib/grappelli/obj_perms_manage.html")

    def test_get_obj_perms_manage_user_template(self):
        gma = self._get_gma()
        self.assertEqual(
            gma.get_obj_perms_manage_user_template(), "admin/guardian/contrib/grappelli/obj_perms_manage_user.html"
        )

    def test_get_obj_perms_manage_group_template(self):
        gma = self._get_gma()
        self.assertEqual(
            gma.get_obj_perms_manage_group_template(), "admin/guardian/contrib/grappelli/obj_perms_manage_group.html"
        )


class GuardedInlineAdminMixinTests(TestCase):
    """Test cases for GuardedInlineAdminMixin functionality."""

    def setUp(self):
        """Set up test data for inline admin tests."""
        self.user = User.objects.create_user("testuser", "test@example.com", "test")
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "admin")
        self.other_user = User.objects.create_user("otheruser", "other@example.com", "other")

        # Create test profile
        self.profile = UserProfile.objects.create(user=self.user, bio="Test bio", phone="555-1234")

        # Ensure permissions exist for UserProfile model
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(UserProfile)

        # Create permissions if they don't exist
        self.permissions = {}
        for action in ["add", "change", "delete", "view"]:
            codename = f"{action}_userprofile"
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                name=f"Can {action} user profile",
                content_type=content_type,
            )
            self.permissions[action] = perm

    def _create_request(self, user):
        """Helper method to create a mock request with user."""
        request = HttpRequest()
        request.user = user
        return request

    def test_inline_has_add_permission_with_object_permission(self):
        """Test that inline respects object-level add permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Without permission, should return False
        self.assertFalse(inline.has_add_permission(request, self.profile))

        # Assign object-level permission
        assign_perm(self.permissions["add"], self.user, self.profile)

        # With permission, should return True
        self.assertTrue(inline.has_add_permission(request, self.profile))

    def test_inline_has_add_permission_global(self):
        """Test that inline respects global add permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Without permission, should return False
        self.assertFalse(inline.has_add_permission(request))

        # Assign global permission
        self.user.user_permissions.add(self.permissions["add"])

        # Refresh user from database to get updated permissions
        self.user = User.objects.get(pk=self.user.pk)
        request = self._create_request(self.user)

        # With permission, should return True
        self.assertTrue(inline.has_add_permission(request))

    def test_inline_has_change_permission_with_object_permission(self):
        """Test that inline respects object-level change permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Without permission, should return False
        self.assertFalse(inline.has_change_permission(request, self.profile))

        # Assign object-level permission
        assign_perm(self.permissions["change"], self.user, self.profile)

        # With permission, should return True
        self.assertTrue(inline.has_change_permission(request, self.profile))

    def test_inline_has_view_permission_with_object_permission(self):
        """Test that inline respects object-level view permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Without permission, should return False
        self.assertFalse(inline.has_view_permission(request, self.profile))

        # Assign object-level permission
        assign_perm(self.permissions["view"], self.user, self.profile)

        # With permission, should return True
        self.assertTrue(inline.has_view_permission(request, self.profile))

    def test_inline_has_delete_permission_with_object_permission(self):
        """Test that inline respects object-level delete permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Without permission, should return False
        self.assertFalse(inline.has_delete_permission(request, self.profile))

        # Assign object-level permission
        assign_perm(self.permissions["delete"], self.user, self.profile)

        # With permission, should return True
        self.assertTrue(inline.has_delete_permission(request, self.profile))

    def test_superuser_has_all_inline_permissions(self):
        """Test that superuser has all inline permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.superuser)

        # Superuser should have all permissions
        self.assertTrue(inline.has_add_permission(request, self.profile))
        self.assertTrue(inline.has_change_permission(request, self.profile))
        self.assertTrue(inline.has_view_permission(request, self.profile))
        self.assertTrue(inline.has_delete_permission(request, self.profile))

    def test_inline_with_none_object(self):
        """Test inline permission methods when obj parameter is None."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Test with obj=None (should check global permissions)
        self.assertFalse(inline.has_add_permission(request, None))
        self.assertFalse(inline.has_change_permission(request, None))
        self.assertFalse(inline.has_view_permission(request, None))
        self.assertFalse(inline.has_delete_permission(request, None))

    def test_inline_permission_denied_for_other_user(self):
        """Test that inline permissions are properly isolated between users."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.other_user)

        # Assign permission only to self.user
        assign_perm(self.permissions["view"], self.user, self.profile)

        # Other user should not have permissions
        self.assertFalse(inline.has_view_permission(request, self.profile))
        self.assertFalse(inline.has_add_permission(request, self.profile))
        self.assertFalse(inline.has_change_permission(request, self.profile))
        self.assertFalse(inline.has_delete_permission(request, self.profile))

    def test_inline_inheritance_order(self):
        """Test that GuardedInlineAdminMixin is properly inherited with Django admin classes."""
        # Test inheritance hierarchy
        self.assertTrue(issubclass(UserProfileInline, GuardedInlineAdminMixin))
        self.assertTrue(issubclass(UserProfileInline, admin.StackedInline))

        # Test that all required methods are available
        inline = UserProfileInline(UserProfile, admin.site)
        self.assertTrue(hasattr(inline, "has_add_permission"))
        self.assertTrue(hasattr(inline, "has_view_permission"))
        self.assertTrue(hasattr(inline, "has_change_permission"))
        self.assertTrue(hasattr(inline, "has_delete_permission"))

    def test_inline_with_tabular_admin(self):
        """Test that GuardedInlineAdminMixin works with TabularInline as well."""

        class UserProfileTabularInline(GuardedInlineAdminMixin, admin.TabularInline):
            model = UserProfile
            extra = 0

        inline = UserProfileTabularInline(UserProfile, admin.site)
        request = self._create_request(self.superuser)

        # Test that all permission methods work with TabularInline
        self.assertTrue(inline.has_add_permission(request, self.user))
        self.assertTrue(inline.has_view_permission(request, self.user))
        self.assertTrue(inline.has_change_permission(request, self.user))
        self.assertTrue(inline.has_delete_permission(request, self.user))

    def test_inline_model_meta_access(self):
        """Test that inline can properly access model meta information."""
        inline = UserProfileInline(UserProfile, admin.site)

        # Test that model meta is accessible
        self.assertEqual(inline.model._meta.model_name, "userprofile")
        self.assertEqual(inline.model._meta.app_label, "testapp")

        # Test permission codename construction
        request = self._create_request(self.user)
        # This should not raise an AttributeError
        try:
            inline.has_add_permission(request, self.user)
            inline.has_view_permission(request, self.user)
            inline.has_change_permission(request, self.user)
            inline.has_delete_permission(request, self.user)
        except AttributeError:
            self.fail("GuardedInlineAdminMixin should be able to access model._meta attributes")

    # Reverse permission tests - ensuring users don't have permissions they shouldn't have
    def test_inline_view_permission_only_denies_other_permissions(self):
        """Test that user with only view permission is denied other permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign only view permission
        assign_perm(self.permissions["view"], self.user, self.profile)

        # Should have view permission
        self.assertTrue(inline.has_view_permission(request, self.profile))

        # Should NOT have other permissions
        self.assertFalse(inline.has_add_permission(request, self.profile))
        self.assertFalse(inline.has_change_permission(request, self.profile))
        self.assertFalse(inline.has_delete_permission(request, self.profile))

    def test_inline_add_permission_only_denies_other_permissions(self):
        """Test that user with only add permission is denied other permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign only add permission
        assign_perm(self.permissions["add"], self.user, self.profile)

        # Should have add permission
        self.assertTrue(inline.has_add_permission(request, self.profile))

        # Should NOT have other permissions
        self.assertFalse(inline.has_view_permission(request, self.profile))
        self.assertFalse(inline.has_change_permission(request, self.profile))
        self.assertFalse(inline.has_delete_permission(request, self.profile))

    def test_inline_change_permission_only_denies_other_permissions(self):
        """Test that user with only change permission is denied other permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign only change permission
        assign_perm(self.permissions["change"], self.user, self.profile)

        # Should have change permission
        self.assertTrue(inline.has_change_permission(request, self.profile))

        # Should NOT have other permissions
        self.assertFalse(inline.has_view_permission(request, self.profile))
        self.assertFalse(inline.has_add_permission(request, self.profile))
        self.assertFalse(inline.has_delete_permission(request, self.profile))

    def test_inline_delete_permission_only_denies_other_permissions(self):
        """Test that user with only delete permission is denied other permissions."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign only delete permission
        assign_perm(self.permissions["delete"], self.user, self.profile)

        # Should have delete permission
        self.assertTrue(inline.has_delete_permission(request, self.profile))

        # Should NOT have other permissions
        self.assertFalse(inline.has_view_permission(request, self.profile))
        self.assertFalse(inline.has_add_permission(request, self.profile))
        self.assertFalse(inline.has_change_permission(request, self.profile))

    def test_inline_partial_permissions_isolation(self):
        """Test that having some permissions doesn't grant others."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign view and add permissions only
        assign_perm(self.permissions["view"], self.user, self.profile)
        assign_perm(self.permissions["add"], self.user, self.profile)

        # Should have assigned permissions
        self.assertTrue(inline.has_view_permission(request, self.profile))
        self.assertTrue(inline.has_add_permission(request, self.profile))

        # Should NOT have unassigned permissions
        self.assertFalse(inline.has_change_permission(request, self.profile))
        self.assertFalse(inline.has_delete_permission(request, self.profile))

    def test_inline_global_vs_object_permission_isolation(self):
        """Test that global permissions don't grant object-level permissions and vice versa."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign global view permission
        self.user.user_permissions.add(self.permissions["view"])
        self.user = User.objects.get(pk=self.user.pk)  # Refresh user
        request = self._create_request(self.user)

        # Should have global view permission (obj=None)
        self.assertTrue(inline.has_view_permission(request, None))

        # Should NOT have object-level permissions for specific object without explicit assignment
        # Note: This might be True if global permissions apply to all objects,
        # but we're testing the isolation principle

        # Now assign object-level add permission
        assign_perm(self.permissions["add"], self.user, self.profile)

        # Should have object-level add permission
        self.assertTrue(inline.has_add_permission(request, self.profile))

        # Should still have global view permission
        self.assertTrue(inline.has_view_permission(request, None))

    def test_inline_permission_revocation(self):
        """Test that removing a permission actually removes access."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Assign all permissions
        for perm in self.permissions.values():
            assign_perm(perm, self.user, self.profile)

        # Verify all permissions are granted
        self.assertTrue(inline.has_view_permission(request, self.profile))
        self.assertTrue(inline.has_add_permission(request, self.profile))
        self.assertTrue(inline.has_change_permission(request, self.profile))
        self.assertTrue(inline.has_delete_permission(request, self.profile))

        # Remove view permission
        remove_perm(self.permissions["view"], self.user, self.profile)

        # Should no longer have view permission
        self.assertFalse(inline.has_view_permission(request, self.profile))

        # Should still have other permissions
        self.assertTrue(inline.has_add_permission(request, self.profile))
        self.assertTrue(inline.has_change_permission(request, self.profile))
        self.assertTrue(inline.has_delete_permission(request, self.profile))

        # Remove all remaining permissions
        remove_perm(self.permissions["add"], self.user, self.profile)
        remove_perm(self.permissions["change"], self.user, self.profile)
        remove_perm(self.permissions["delete"], self.user, self.profile)

        # Should have no permissions
        self.assertFalse(inline.has_view_permission(request, self.profile))
        self.assertFalse(inline.has_add_permission(request, self.profile))
        self.assertFalse(inline.has_change_permission(request, self.profile))
        self.assertFalse(inline.has_delete_permission(request, self.profile))

    def test_inline_different_objects_permission_isolation(self):
        """Test that permissions on one object don't grant access to another object."""
        inline = UserProfileInline(UserProfile, admin.site)
        request = self._create_request(self.user)

        # Create another user and profile
        other_user = User.objects.create_user("another", "another@example.com", "another")
        other_profile = UserProfile.objects.create(user=other_user, bio="Other bio", phone="555-9999")

        # Assign permissions only to self.profile
        assign_perm(self.permissions["view"], self.user, self.profile)
        assign_perm(self.permissions["change"], self.user, self.profile)

        # Should have permissions on self.profile
        self.assertTrue(inline.has_view_permission(request, self.profile))
        self.assertTrue(inline.has_change_permission(request, self.profile))

        # Should NOT have permissions on other_profile
        self.assertFalse(inline.has_view_permission(request, other_profile))
        self.assertFalse(inline.has_change_permission(request, other_profile))
        self.assertFalse(inline.has_add_permission(request, other_profile))
        self.assertFalse(inline.has_delete_permission(request, other_profile))
