from django.test import TestCase
from django.contrib.auth.models import User, Group, AnonymousUser
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from guardian.decorators import permission_required, permission_required_or_403
from guardian.exceptions import GuardianError
from guardian.shortcuts import assign


class PermissionRequiredTest(TestCase):

    fixtures = ['tests.json']

    def setUp(self):
        self.anon = AnonymousUser()
        self.user = User.objects.get(username='jack')
        self.group = Group.objects.get(name='jackGroup')

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

    def test_anonymous_user_wrong_app(self):

        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertTrue(isinstance(dummy_view(request), HttpResponseForbidden))

    def test_anonymous_user_wrong_codename(self):

        request = self._get_request()

        @permission_required_or_403('auth.wrong_codename')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertTrue(isinstance(dummy_view(request), HttpResponseForbidden))

    def test_anonymous_user(self):

        request = self._get_request()

        @permission_required_or_403('auth.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertTrue(isinstance(dummy_view(request), HttpResponseForbidden))

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

