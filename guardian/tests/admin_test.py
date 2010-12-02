from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_perms_for_model
from guardian.tests.app.models import Keycard


class AdminTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com',
            'admin')
        self.user = User.objects.create_user('joe', 'joe@example.com', 'joe')
        self.group = Group.objects.create(name='group')
        self.client = Client()
        self.keycard = Keycard.objects.create(key='admin_tests')

    def tearDown(self):
        self.client.logout()

    def _login_superuser(self):
        self.client.login(username='admin', password='admin')

    def test_view_manage_wrong_obj(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/-10/permissions/user-manage/%d/' % \
            self.user.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.keycard)

    def test_view_manage_wrong_user(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/user-manage/-10/' % \
            self.keycard.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view_manage_user_form(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'user': self.user.username, 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = url + 'user-manage/%d/' % self.user.id
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_user_form_wrong_user(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'user': 'wrong-user', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_form_wrong_field(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'user': '<xss>', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_form_empty_user(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'user': '', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_wrong_perms(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/user-manage/%d/' % \
            (self.keycard.id, self.user.id)
        perms = ['change_user'] # This is not keycard-related permission
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('permissions' in response.context['form'].errors)

    def test_view_manage_user(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/user-manage/%d/' % \
            (self.keycard.id, self.user.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = set([c[0] for c in
            response.context['form'].fields['permissions'].choices])
        self.assertEqual(
            set([ p.codename for p in get_perms_for_model(self.keycard)]),
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ['change_keycard', 'can_use_keycard']
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.user, self.keycard)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ['can_use_keycard']
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.user, self.keycard)),
            set(perms),
        )

    def test_view_manage_group_form(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'group': self.group.name, 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = url + 'group-manage/%d/' % self.group.id
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_group_form_wrong_group(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'group': 'wrong-group', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_form_wrong_field(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'group': '<xss>', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_form_empty_group(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/' % self.keycard.id
        data = {'group': '', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_wrong_perms(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/group-manage/%d/' % \
            (self.keycard.id, self.group.id)
        perms = ['change_user'] # This is not keycard-related permission
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('permissions' in response.context['form'].errors)

    def test_view_manage_group(self):
        self._login_superuser()
        url = '/admin/guardian/keycard/%d/permissions/group-manage/%d/' % \
            (self.keycard.id, self.group.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = set([c[0] for c in
            response.context['form'].fields['permissions'].choices])
        self.assertEqual(
            set([ p.codename for p in get_perms_for_model(self.keycard)]),
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ['change_keycard', 'can_use_keycard']
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.keycard)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ['can_use_keycard']
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.keycard)),
            set(perms),
        )



class GuardedModelAdminTests(TestCase):

    def _get_gma(self, attrs=None, name=None, model=None):
        """
        Returns ``GuardedModelAdmin`` instance.
        """
        attrs = attrs or {}
        name = name or 'GMA'
        model = model or User
        GMA = type(name, (GuardedModelAdmin,), attrs)
        gma = GMA(model, admin.site)
        return gma

    def test_obj_perms_manage_template_attr(self):
        attrs = {'obj_perms_manage_template': 'foobar.html'}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_template(), 'foobar.html')

    def test_obj_perms_manage_user_template_attr(self):
        attrs = {'obj_perms_manage_user_template': 'foobar.html'}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_user_template(), 'foobar.html')

    def test_obj_perms_manage_user_form_attr(self):
        attrs = {'obj_perms_manage_user_form': forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_user_form(), forms.Form)

    def test_obj_perms_manage_group_template_attr(self):
        attrs = {'obj_perms_manage_group_template': 'foobar.html'}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_group_template(),
            'foobar.html')

    def test_obj_perms_manage_group_form_attr(self):
        attrs = {'obj_perms_manage_group_form': forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_group_form(), forms.Form)

