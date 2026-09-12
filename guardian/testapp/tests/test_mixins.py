from types import GeneratorType
from unittest import mock, skipIf
import warnings

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.views.generic import ListView, View

from guardian.mixins import (
    _ASYNC_VIEWS_SUPPORTED,
    LoginRequiredMixin,
    PermissionListMixin,
    PermissionRequiredMixin,
)
from guardian.shortcuts import assign_perm

from ..models import Post


class DatabaseRemovedError(Exception):
    pass


class RemoveDatabaseView(View):
    def get(self, request, *args, **kwargs):
        raise DatabaseRemovedError("You've just allowed db to be removed!")


class PermissionTestView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = "testapp.change_post"
    object = None  # should be set at each tests explicitly


class NoObjectView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = "testapp.change_post"


class GlobalNoObjectView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = "testapp.add_post"
    accept_global_perms = True


class PostPermissionListView(PermissionListMixin, ListView):
    model = Post
    permission_required = "testapp.change_post"
    template_name = "list.html"


class AsyncPermissionView(PermissionRequiredMixin, View):
    permission_required = "testapp.change_post"
    raise_exception = True

    async def get(self, request, *args, **kwargs):
        return HttpResponse("some html")


def check_fail_handler(obj):
    """Hook used by the tests to assert `on_permission_check_fail` was called."""


class AsyncPermissionObjectView(AsyncPermissionView):
    async def aget_permission_object(self):
        return await Post.objects.aget(title="foo-post-title")

    def on_permission_check_fail(self, request, response, obj=None):
        check_fail_handler(obj)


@skipIf(not _ASYNC_VIEWS_SUPPORTED, "Asynchronous class-based views require Django >= 4.2")
class AsyncPermissionRequiredMixinTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.post = Post.objects.create(title="foo-post-title")
        cls.user = get_user_model().objects.create_user("joe", "joe@doe.com", "doe")

    def setUp(self):
        self.factory = RequestFactory()

    @staticmethod
    def dispatch(view, request, **kwargs):
        """Run a view's asynchronous `dispatch()` from a synchronous test."""

        async def run():
            return await view.dispatch(request, **kwargs)

        return async_to_sync(run)()

    def test_authorized_user_can_access_async_view(self):
        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = AsyncPermissionObjectView()
        view.setup(request)
        response = self.dispatch(view, request)
        self.assertEqual(response.content, b"some html")

    def test_default_aget_permission_object_falls_back_to_sync_get_object(self):
        class AsyncViewWithSyncGetObject(AsyncPermissionView):
            def get_object(inner_self):
                return self.post

        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = AsyncViewWithSyncGetObject()
        view.setup(request)
        response = self.dispatch(view, request)
        self.assertEqual(response.content, b"some html")

    @mock.patch("guardian.testapp.tests.test_mixins.check_fail_handler")
    def test_unauthorized_user_cannot_access_async_view(self, check_fail):
        request = self.factory.get("/")
        request.user = self.user
        view = AsyncPermissionObjectView()
        view.setup(request)
        with self.assertRaises(PermissionDenied):
            self.dispatch(view, request)
        check_fail.assert_called_once_with(self.post)

    def test_unauthorized_user_is_redirected_from_async_view(self):
        request = self.factory.get("/")
        request.user = self.user
        view = AsyncPermissionObjectView()
        view.setup(request)
        view.raise_exception = False
        response = self.dispatch(view, request)
        self.assertEqual(response.status_code, 302)

    def test_disallowed_http_method_works_in_async_view(self):
        request = self.factory.post("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = AsyncPermissionObjectView()
        view.setup(request)
        response = self.dispatch(view, request)
        self.assertEqual(response.status_code, 405)

    def test_async_get_object_is_awaited(self):
        class AsyncViewWithAsyncGetObject(AsyncPermissionView):
            async def get_object(self):
                return await Post.objects.aget(title="foo-post-title")

        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = AsyncViewWithAsyncGetObject()
        view.setup(request)
        response = self.dispatch(view, request)
        self.assertEqual(response.content, b"some html")

    def test_async_get_permission_object_is_awaited(self):
        class AsyncViewWithAsyncGetPermissionObject(AsyncPermissionView):
            async def get_permission_object(self):
                return await Post.objects.aget(title="foo-post-title")

        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = AsyncViewWithAsyncGetPermissionObject()
        view.setup(request)
        response = self.dispatch(view, request)
        self.assertEqual(response.content, b"some html")

    def test_sync_hooks_can_query_the_database_in_async_view(self):
        """Overridden synchronous hooks run in a thread, so ORM access is allowed."""

        class AsyncViewQueryingHooks(AsyncPermissionObjectView):
            def get_required_permissions(inner_self, request=None):
                Post.objects.count()
                return super().get_required_permissions(request)

            def get_object_permission_denied_message(inner_self):
                return Post.objects.get(pk=self.post.pk).title

        request = self.factory.get("/")
        request.user = self.user
        view = AsyncViewQueryingHooks()
        view.setup(request)
        with self.assertRaisesMessage(PermissionDenied, "foo-post-title"):
            self.dispatch(view, request)

        request.user.add_obj_perm("change_post", self.post)
        response = self.dispatch(view, request)
        self.assertEqual(response.content, b"some html")

    def test_async_view_is_detected(self):
        self.assertTrue(AsyncPermissionView.view_is_async)
        self.assertFalse(PermissionTestView.view_is_async)


class TestViewMixins(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title="foo-post-title")
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user("joe", "joe@doe.com", "doe")
        self.client.login(username="joe", password="doe")

    def test_permission_is_checked_before_view_is_computed(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get("/")
        request.user = self.user
        # View.object is set
        view = PermissionTestView.as_view(object=self.post)
        response = view(request)
        self.assertEqual(response.status_code, 302)

        # View.get_object returns object
        PermissionTestView.get_object = lambda instance: self.post
        view = PermissionTestView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        del PermissionTestView.get_object

    def test_permission_is_checked_before_view_is_computed_perm_denied_raised(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get("/")
        request.user = self.user
        view = PermissionTestView.as_view(raise_exception=True, object=self.post)
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_permission_required_view_configured_wrongly(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = PermissionTestView.as_view(permission_required=None, object=self.post)
        with self.assertRaises(ImproperlyConfigured):
            view(request)

    def test_permission_required(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = PermissionTestView.as_view(object=self.post)
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_permission_required_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it has none
        """

        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        view = NoObjectView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_permission_required_global_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it not set and **no** global permission
        """

        request = self.factory.get("/")
        request.user = self.user
        view = GlobalNoObjectView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_permission_granted_global_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it not set and **has** global permission
        """

        request = self.factory.get("/")
        request.user = self.user
        assign_perm("testapp.add_post", request.user)
        view = GlobalNoObjectView.as_view()
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_permission_required_as_list(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """

        global PermissionTestView

        class SecretView(PermissionTestView):
            on_permission_check_fail = mock.Mock()

        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)
        SecretView.permission_required = ["testapp.change_post", "testapp.add_post"]
        view = SecretView.as_view(object=self.post)
        response = view(request)
        self.assertEqual(response.status_code, 302)
        SecretView.on_permission_check_fail.assert_called_once_with(request, response, obj=self.post)

        request.user.add_obj_perm("add_post", self.post)
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_login_required_mixin(self):
        class SecretView(LoginRequiredMixin, View):
            redirect_field_name = "foobar"
            login_url = "/let-me-in/"

            def get(self, request):
                return HttpResponse("secret-view")

        request = self.factory.get("/some-secret-page/")
        request.user = AnonymousUser()

        view = SecretView.as_view()

        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/let-me-in/?foobar=/some-secret-page/")

        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"secret-view")

    def test_list_permission(self):
        request = self.factory.get("/some-secret-list/")
        request.user = AnonymousUser()

        view = PostPermissionListView.as_view()

        response = view(request)
        self.assertNotContains(response, b"foo-post-title")

        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)

        response = view(request)
        self.assertContains(response, b"foo-post-title")

    def test_any_perm_parameter(self):
        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("view_post", self.post)
        self.assertIs(request.user.has_perm("view_post", self.post), True)
        self.assertIs(request.user.has_perm("change_post", self.post), False)
        # success way
        view = PermissionTestView.as_view(
            any_perm=True,
            permission_required=["change_post", "view_post"],
            object=self.post,
        )
        with self.assertRaises(DatabaseRemovedError):
            view(request)
        # fail way
        view = PermissionTestView.as_view(
            any_perm=False,
            permission_required=["change_post", "view_post"],
            object=self.post,
        )
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_get_objects_for_user_kwargs_raises_deprecation_warning(self):
        """The old method should raise a deprecation warning.

        This test should be removed when the deprecated method is removed.

        See Also:
            https://docs.python.org/3.9/library/warnings.html#testing-warnings
        """
        request = self.factory.get("/")
        request.user = self.user
        request.user.add_obj_perm("change_post", self.post)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            qs = PostPermissionListView.model.objects.all()
            PostPermissionListView(request=request).get_get_objects_for_user_kwargs(qs)

            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)

    def test_permission_required_iterable_types_validation(self):
        """Ensure that valid iterable types (list, tuple, set) still work after the generator fix."""
        request = self.factory.get("/")
        request.user = self.user

        # Test with list
        view = PermissionTestView()
        view.permission_required = ["testapp.change_post", "testapp.view_post"]
        perms = view.get_required_permissions()
        self.assertEqual(perms, ["testapp.change_post", "testapp.view_post"])

        # Test with tuple
        view.permission_required = ("testapp.change_post", "testapp.view_post")
        perms = view.get_required_permissions()
        self.assertEqual(perms, ["testapp.change_post", "testapp.view_post"])

        # Test with set (order may vary)
        view.permission_required = {"testapp.change_post", "testapp.view_post"}
        perms = view.get_required_permissions()
        self.assertEqual(set(perms), {"testapp.change_post", "testapp.view_post"})

        # Test with string (single permission)
        view.permission_required = "testapp.change_post"
        perms = view.get_required_permissions()
        self.assertEqual(perms, ["testapp.change_post"])

    def test_permission_required_generator_deprecation(self):
        """Test that generators trigger deprecation warning instead of exception.

        Generators can only be consumed once and would return empty list on second iteration,
        potentially granting unauthorized access. This feature is deprecated and will be removed in v4.
        """

        # Test PermissionRequiredMixin
        class GeneratorTestView(PermissionRequiredMixin, View):
            def get(self, request):
                return HttpResponse("secret content")

        generator_perms = (perm for perm in ["testapp.change_post", "testapp.view_post"])
        self.assertIsInstance(generator_perms, GeneratorType)

        view = GeneratorTestView()
        view.permission_required = generator_perms

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            perms = view.get_required_permissions()

            # Should have issued a deprecation warning
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated and will be removed in v4", str(w[0].message))
            self.assertIn("security issues", str(w[0].message))
            self.assertIn("Use a list or tuple instead", str(w[0].message))

            # Should still return the permissions (converted from generator)
            self.assertEqual(perms, ["testapp.change_post", "testapp.view_post"])

    def test_permission_list_mixin_generator_deprecation(self):
        """Test that PermissionListMixin also triggers deprecation warning for generators."""
        from types import GeneratorType

        # Test PermissionListMixin
        class GeneratorListView(PermissionListMixin, ListView):
            model = Post
            template_name = "list.html"

        generator_perms = (perm for perm in ["testapp.change_post", "testapp.view_post"])
        self.assertIsInstance(generator_perms, GeneratorType)

        view = GeneratorListView()
        view.permission_required = generator_perms

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            perms = view.get_required_permissions()

            # Should have issued a deprecation warning
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated and will be removed in v4", str(w[0].message))
            self.assertIn("security issues", str(w[0].message))

            # Should still return the permissions (converted from generator)
            self.assertEqual(perms, ["testapp.change_post", "testapp.view_post"])
