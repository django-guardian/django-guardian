from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.client import RequestFactory
from django.views.generic import View

from guardian.view_mixins import PermissionRequiredMixin


class DatabaseRemovedError(Exception):
    pass


class RemoveDatabaseView(View):
    def get(self, request, *args, **kwargs):
        raise DatabaseRemovedError("You've just allowed db to be removed!")

class TestView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = 'contenttypes.change_contenttype'
    object = None # should be set at each tests explicitly


class TestViewMixins(TestCase):

    def setUp(self):
        self.ctype = ContentType.objects.create(name='foo', model='bar',
            app_label='fake-for-guardian-tests')
        self.factory = RequestFactory()
        self.user = User.objects.create_user('joe', 'joe@doe.com', 'doe')
        self.client.login(username='joe', password='doe')

    def test_permission_is_checked_before_view_is_computed(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        view = TestView.as_view(object=self.ctype)
        response = view(request)
        self.assertEqual(response.status_code, 403)

