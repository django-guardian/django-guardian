import mock
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User, Group, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import TemplateDoesNotExist
from guardian.decorators import permission_required, permission_required_or_403
from guardian.exceptions import GuardianError
from guardian.shortcuts import assign


class PermissionRequiredTest(TestCase):

    fixtures = ['tests.json']

    def setUp(self):
        self.anon = AnonymousUser()
        self.user = User.objects.get_or_create(username='jack')[0]
        self.group = Group.objects.get_or_create(name='jackGroup')[0]

    def _get_request(self, user=None):
        if user is None:
            user = AnonymousUser()
        request = HttpRequest()
        request.user = user
        return request

    def test_no_args(self):

        try:
            @permission_required
            def dummy_view(request):
                return HttpResponse('dummy_view')
        except GuardianError:
            pass
        else:
            self.fail("Trying to decorate using permission_required without "
                "permission as first argument should raise exception")

    def test_RENDER_403_is_false(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        with mock.patch('guardian.conf.settings.RENDER_403', False):
            response = dummy_view(request)
            self.assertEqual(response.content, '')
            self.assertTrue(isinstance(response, HttpResponseForbidden))

    @mock.patch('guardian.conf.settings.RENDER_403', True)
    def test_TEMPLATE_403_setting(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        with mock.patch('guardian.conf.settings.TEMPLATE_403', 'dummy403.html'):
            response = dummy_view(request)
            self.assertEqual(response.content, 'foobar403\n')

    @mock.patch('guardian.conf.settings.RENDER_403', True)
    def test_403_response_is_empty_if_template_cannot_be_found(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        with mock.patch('guardian.conf.settings.TEMPLATE_403',
            '_non-exisitng-403.html'):
            response = dummy_view(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.content, '')

    @mock.patch('guardian.conf.settings.RENDER_403', True)
    def test_403_response_raises_error_if_debug_is_turned_on(self):
        org_DEBUG = settings.DEBUG
        settings.DEBUG = True
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        with mock.patch('guardian.conf.settings.TEMPLATE_403',
            '_non-exisitng-403.html'):
            self.assertRaises(TemplateDoesNotExist, dummy_view, request)
        settings.DEBUG = org_DEBUG

    @mock.patch('guardian.conf.settings.RENDER_403', False)
    @mock.patch('guardian.conf.settings.RAISE_403', True)
    def test_RAISE_403_setting_is_true(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        self.assertRaises(PermissionDenied, dummy_view, request)

    def test_anonymous_user_wrong_app(self):

        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_anonymous_user_wrong_codename(self):

        request = self._get_request()

        @permission_required_or_403('auth.wrong_codename')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_anonymous_user(self):

        request = self._get_request()

        @permission_required_or_403('auth.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_wrong_lookup_variables_number(self):

        request = self._get_request()

        try:
            @permission_required_or_403('auth.change_user', (User, 'username'))
            def dummy_view(request, username):
                pass
            dummy_view(request, username='jack')
        except GuardianError:
            pass
        else:
            self.fail("If lookup variables are passed they must be tuple of: "
                "(ModelClass/app_label.ModelClass/queryset, "
                "<pair of lookup_string and view_arg>)\n"
                "Otherwise GuardianError should be raised")

    def test_wrong_lookup_variables(self):

        request = self._get_request()

        args = (
            (2010, 'username', 'username'),
            ('User', 'username', 'username'),
            (User, 'username', 'no_arg'),
        )
        for tup in args:
            try:
                @permission_required_or_403('auth.change_user', tup)
                def show_user(request, username):
                    user = get_object_or_404(User, username=username)
                    return HttpResponse("It's %s here!" % user.username)
                show_user(request, 'jack')
            except GuardianError:
                pass
            else:
                self.fail("Wrong arguments given but GuardianError not raised")

    def test_user_has_no_access(self):

        request = self._get_request()

        @permission_required_or_403('auth.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_user_has_access(self):

        perm = 'auth.change_user'
        joe, created = User.objects.get_or_create(username='joe')
        assign(perm, self.user, obj=joe)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            'auth.User', 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'dummy_view')

    def test_user_has_obj_access_even_if_we_also_check_for_global(self):

        perm = 'auth.change_user'
        joe, created = User.objects.get_or_create(username='joe')
        assign(perm, self.user, obj=joe)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            'auth.User', 'username', 'username'), accept_global_perms=True)
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'dummy_view')

    def test_user_has_no_obj_perm_access(self):

        perm = 'auth.change_user'
        joe, created = User.objects.get_or_create(username='joe')

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            'auth.User', 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 403)

    def test_user_has_global_perm_access_but_flag_not_set(self):

        perm = 'auth.change_user'
        joe, created = User.objects.get_or_create(username='joe')
        assign(perm, self.user)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            'auth.User', 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 403)

    def test_user_has_global_perm_access(self):

        perm = 'auth.change_user'
        joe, created = User.objects.get_or_create(username='joe')
        assign(perm, self.user)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            'auth.User', 'username', 'username'), accept_global_perms=True)
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'dummy_view')

    def test_model_lookup(self):

        request = self._get_request(self.user)

        perm = 'auth.change_user'
        joe, created = User.objects.get_or_create(username='joe')
        assign(perm, self.user, obj=joe)

        models = (
            'auth.User',
            User,
            User.objects.filter(is_active=True),
        )
        for model in models:
            @permission_required_or_403(perm, (model, 'username', 'username'))
            def dummy_view(request, username):
                get_object_or_404(User, username=username)
                return HttpResponse('hello')
            response = dummy_view(request, username=joe.username)
            self.assertEqual(response.content, 'hello')

    def test_redirection(self):

        request = self._get_request(self.user)

        foo = User.objects.create(username='foo')
        foobar = Group.objects.create(name='foobar')
        foo.groups.add(foobar)

        @permission_required('auth.change_group',
            (User, 'groups__name', 'group_name'),
            login_url='/foobar/')
        def dummy_view(request, group_name):
            pass
        response = dummy_view(request, group_name='foobar')
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertTrue(response._headers['location'][1].startswith(
            '/foobar/'))

