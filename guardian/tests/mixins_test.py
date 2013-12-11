from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.views.generic import View

from guardian.compat import get_user_model
from guardian.compat import mock
from guardian.mixins import LoginRequiredMixin
from guardian.mixins import PermissionRequiredMixin

class DatabaseRemovedError(Exception):
    pass


class RemoveDatabaseView(View):
    def get(self, request, *args, **kwargs):
        raise DatabaseRemovedError("You've just allowed db to be removed!")

class TestView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = 'contenttypes.change_contenttype'
    object = None # should be set at each tests explicitly

class NoObjectView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = 'contenttypes.change_contenttype'

class TestViewMixins(TestCase):

    def setUp(self):
        self.ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            'joe', 'joe@doe.com', 'doe')
        self.client.login(username='joe', password='doe')

    def test_permission_is_checked_before_view_is_computed(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        # View.object is set
        view = TestView.as_view(object=self.ctype)
        response = view(request)
        self.assertEqual(response.status_code, 302)

        # View.get_object returns object
        TestView.get_object = lambda instance: self.ctype
        view = TestView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        del TestView.get_object

    def test_permission_is_checked_before_view_is_computed_perm_denied_raised(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        view = TestView.as_view(raise_exception=True, object=self.ctype)
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_permission_required_view_configured_wrongly(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_contenttype', self.ctype)
        view = TestView.as_view(permission_required=None, object=self.ctype)
        with self.assertRaises(ImproperlyConfigured):
            view(request)

    def test_permission_required(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_contenttype', self.ctype)
        view = TestView.as_view(object=self.ctype)
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_permission_required_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it has none
        """

        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_contenttype', self.ctype)
        view = NoObjectView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_permission_required_as_list(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """

        global TestView
        class SecretView(TestView):
            on_permission_check_fail = mock.Mock()

        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_contenttype', self.ctype)
        SecretView.permission_required = ['contenttypes.change_contenttype',
            'contenttypes.add_contenttype']
        view = SecretView.as_view(object=self.ctype)
        response = view(request)
        self.assertEqual(response.status_code, 302)
        SecretView.on_permission_check_fail.assert_called_once_with(request,
            response, obj=self.ctype)

        request.user.add_obj_perm('add_contenttype', self.ctype)
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_login_required_mixin(self):

        class SecretView(LoginRequiredMixin, View):
            redirect_field_name = 'foobar'
            login_url = '/let-me-in/'

            def get(self, request):
                return HttpResponse('secret-view')

        request = self.factory.get('/some-secret-page/')
        request.user = AnonymousUser()

        view = SecretView.as_view()

        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
            '/let-me-in/?foobar=/some-secret-page/')

        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'secret-view')

