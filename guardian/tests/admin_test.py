import copy

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_perms_for_model

class ContentTypeGuardedAdmin(GuardedModelAdmin):
    pass

admin.site.register(ContentType, ContentTypeGuardedAdmin)


class AdminTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com',
            'admin')
        self.user = User.objects.create_user('joe', 'joe@example.com', 'joe')
        self.group = Group.objects.create(name='group')
        self.client = Client()
        self.obj = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        self.obj_info = self.obj._meta.app_label, self.obj._meta.module_name

    def tearDown(self):
        self.client.logout()

    def _login_superuser(self):
        self.client.login(username='admin', password='admin')

    def test_view_manage_wrong_obj(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
                kwargs={'object_pk': "000000000000000000000000", 'user_id': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.obj)

    def test_view_manage_wrong_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
            kwargs={'object_pk': self.obj.pk, 'user_id': "000000000000000000000000"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view_manage_user_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'user': self.user.username, 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_user' %
            self.obj_info, kwargs={'object_pk': self.obj.pk,
                'user_id': self.user.id})
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_negative_user_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        self.user = User.objects.create(username='negative_id_user', id="000000000000000000000000")
        data = {'user': self.user.username, 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_user' %
            self.obj_info, args=[self.obj.pk, self.user.id])
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_user_form_wrong_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'user': 'wrong-user', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_form_wrong_field(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'user': '<xss>', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_form_empty_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'user': '', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_wrong_perms(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
            args=[self.obj.pk, self.user.id])
        perms = ['change_user'] # This is not self.obj related permission
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('permissions' in response.context['form'].errors)

    def test_view_manage_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
            args=[self.obj.pk, self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = set([c[0] for c in
            response.context['form'].fields['permissions'].choices])
        self.assertEqual(
            set([ p.codename for p in get_perms_for_model(self.obj)]),
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ['change_%s' % self.obj_info[1], 'delete_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.user, self.obj)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ['change_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.user, self.obj)),
            set(perms),
        )

    def test_view_manage_group_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'group': self.group.name, 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_group' %
            self.obj_info, args=[self.obj.pk, self.group.id])
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_negative_group_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        self.group = Group.objects.create(name='neagive_id_group', id="000000000000000000000000")
        data = {'group': self.group.name, 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_group' %
            self.obj_info, args=[self.obj.pk, self.group.id])
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_group_form_wrong_group(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'group': 'wrong-group', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_form_wrong_field(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'group': '<xss>', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_form_empty_group(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
            args=[self.obj.pk])
        data = {'group': '', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_wrong_perms(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_group' %
            self.obj_info, args=[self.obj.pk, self.group.id])
        perms = ['change_user'] # This is not self.obj related permission
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('permissions' in response.context['form'].errors)

    def test_view_manage_group(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_group' %
            self.obj_info, args=[self.obj.pk, self.group.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = set([c[0] for c in
            response.context['form'].fields['permissions'].choices])
        self.assertEqual(
            set([ p.codename for p in get_perms_for_model(self.obj)]),
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ['change_%s' % self.obj_info[1], 'delete_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.obj)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ['delete_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.obj)),
            set(perms),
        )

if 'django.contrib.admin' not in settings.INSTALLED_APPS:
    # Skip admin tests if admin app is not registered
    # we simpy clean up AdminTests class ...
    AdminTests = type('AdminTests', (TestCase,), {})


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

"""
class GrappelliGuardedModelAdminTests(TestCase):

    org_settings = None

    def _get_gma(self, attrs=None, name=None, model=None):
        attrs = attrs or {}
        name = name or 'GMA'
        model = model or User
        GMA = type(name, (GuardedModelAdmin,), attrs)
        gma = GMA(model, admin.site)
        return gma

    def setUp(self):
        self.org_settings = copy.copy(settings)
        settings.INSTALLED_APPS = ['grappelli'] + list(settings.INSTALLED_APPS)

    def tearDown(self):
        globals()['settings'] = copy.copy(self.org_settings)

    def test_get_obj_perms_manage_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_template(),
            'admin/guardian/contrib/grappelli/obj_perms_manage.html')

    def test_get_obj_perms_manage_user_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_user_template(),
            'admin/guardian/contrib/grappelli/obj_perms_manage_user.html')

    def test_get_obj_perms_manage_group_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_group_template(),
            'admin/guardian/contrib/grappelli/obj_perms_manage_group.html')
"""
