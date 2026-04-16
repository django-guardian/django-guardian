"""
Tests for the queryset double-evaluation fix in _get_pks_model_and_ctype and prefetch_perms.

Previously, when a QuerySet was passed to prefetch_perms:
  1. _get_pks_model_and_ctype called objects.values_list('pk', flat=True) → 1st DB query
  2. prefetch_perms iterated `for obj in objects:` → 2nd DB query

After the fix, _get_pks_model_and_ctype iterates the queryset directly via
`[force_str(obj.pk) for obj in objects]`, which populates Django's internal
_result_cache. The second iteration in prefetch_perms then uses the cache
instead of hitting the database again.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils.encoding import force_str

from guardian.core import ObjectPermissionChecker, _get_pks_model_and_ctype
from guardian.shortcuts import assign_perm
from guardian.testapp.models import Project

User = get_user_model()


class GetPksModelAndCtypeTests(TestCase):
    """Tests for the _get_pks_model_and_ctype helper function."""

    def test_with_queryset_returns_correct_pks(self):
        """PKs returned from a QuerySet input should match the objects' PKs."""
        projects = [Project.objects.create(name=f"proj{i}") for i in range(3)]
        qs = Project.objects.filter(pk__in=[p.pk for p in projects]).order_by("pk")

        pks, model, ctype = _get_pks_model_and_ctype(qs)

        expected_pks = [force_str(p.pk) for p in projects]
        self.assertEqual(sorted(pks), sorted(expected_pks))
        self.assertEqual(model, Project)
        self.assertEqual(ctype, ContentType.objects.get_for_model(Project))

    def test_with_list_returns_correct_pks(self):
        """PKs returned from a list input should match the objects' PKs."""
        projects = [Project.objects.create(name=f"proj{i}") for i in range(3)]

        pks, model, ctype = _get_pks_model_and_ctype(projects)

        expected_pks = [force_str(p.pk) for p in projects]
        self.assertEqual(pks, expected_pks)
        self.assertEqual(model, Project)
        self.assertEqual(ctype, ContentType.objects.get_for_model(Project))

    def test_queryset_and_list_produce_same_results(self):
        """Both QuerySet and list inputs should produce identical results."""
        projects = [Project.objects.create(name=f"proj{i}") for i in range(5)]
        qs = Project.objects.filter(pk__in=[p.pk for p in projects]).order_by("pk")
        projects_sorted = sorted(projects, key=lambda p: p.pk)

        pks_qs, model_qs, ctype_qs = _get_pks_model_and_ctype(qs)
        pks_list, model_list, ctype_list = _get_pks_model_and_ctype(projects_sorted)

        self.assertEqual(pks_qs, pks_list)
        self.assertEqual(model_qs, model_list)
        self.assertEqual(ctype_qs, ctype_list)

    def test_with_empty_queryset(self):
        """Empty QuerySet should return empty pks list."""
        qs = Project.objects.none()
        pks, model, ctype = _get_pks_model_and_ctype(qs)

        self.assertEqual(pks, [])
        self.assertEqual(model, Project)

    def test_with_empty_list(self):
        """Empty list should return empty pks and None model/ctype."""
        pks, model, ctype = _get_pks_model_and_ctype([])

        self.assertEqual(pks, [])
        self.assertIsNone(model)
        self.assertIsNone(ctype)

    def test_with_single_object_queryset(self):
        """Single object QuerySet should work correctly."""
        project = Project.objects.create(name="single")
        qs = Project.objects.filter(pk=project.pk)

        pks, model, ctype = _get_pks_model_and_ctype(qs)

        self.assertEqual(pks, [force_str(project.pk)])
        self.assertEqual(model, Project)

    def test_with_single_object_list(self):
        """Single object list should work correctly."""
        project = Project.objects.create(name="single")

        pks, model, ctype = _get_pks_model_and_ctype([project])

        self.assertEqual(pks, [force_str(project.pk)])
        self.assertEqual(model, Project)

    def test_queryset_is_cached_after_call(self):
        """After _get_pks_model_and_ctype, the QuerySet's _result_cache should be populated."""
        projects = [Project.objects.create(name=f"proj{i}") for i in range(3)]
        qs = Project.objects.filter(pk__in=[p.pk for p in projects])

        # Before the call, cache should be None
        self.assertIsNone(qs._result_cache)

        _get_pks_model_and_ctype(qs)

        # After the call, cache should be populated
        self.assertIsNotNone(qs._result_cache)
        self.assertEqual(len(qs._result_cache), 3)

    def test_pks_are_strings(self):
        """All returned PKs should be strings (via force_str)."""
        projects = [Project.objects.create(name=f"proj{i}") for i in range(3)]
        qs = Project.objects.filter(pk__in=[p.pk for p in projects])

        pks, _, _ = _get_pks_model_and_ctype(qs)

        for pk in pks:
            self.assertIsInstance(pk, str)

    def test_with_generator_input(self):
        """Generator input should be handled by the else branch (not QuerySet)."""
        projects = [Project.objects.create(name=f"proj{i}") for i in range(3)]

        def gen():
            yield from projects

        pks, model, ctype = _get_pks_model_and_ctype(gen())

        expected_pks = [force_str(p.pk) for p in projects]
        self.assertEqual(pks, expected_pks)
        self.assertEqual(model, Project)


class QuerySetDoubleEvaluationTests(TestCase):
    """
    Tests that verify the QuerySet is only evaluated once (no double DB hit)
    when passed to prefetch_perms.
    """

    def setUp(self):
        self.user = User.objects.create(username="testuser", is_active=True)
        self.projects = [Project.objects.create(name=f"project{i}") for i in range(5)]
        assign_perm("change_project", self.user, self.projects[0])
        assign_perm("change_project", self.user, self.projects[1])
        assign_perm("delete_project", self.user, self.projects[2])

    @override_settings(DEBUG=True)
    def test_queryset_single_evaluation_in_get_pks(self):
        """_get_pks_model_and_ctype should only cause one DB query for a QuerySet."""
        # Warm the ContentType cache to avoid counting that lookup
        ContentType.objects.get_for_model(Project)

        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])

        query_count_before = len(connection.queries)
        _get_pks_model_and_ctype(qs)
        query_count_after = len(connection.queries)

        # Only 1 query should be executed (SELECT for the objects)
        self.assertEqual(query_count_after - query_count_before, 1)

    @override_settings(DEBUG=True)
    def test_queryset_no_extra_query_on_second_iteration(self):
        """After _get_pks_model_and_ctype evaluates the QS, iterating again should not hit DB."""
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])

        _get_pks_model_and_ctype(qs)

        # Second iteration should use cache
        query_count_before = len(connection.queries)
        for obj in qs:
            pass  # iterate without hitting DB
        query_count_after = len(connection.queries)

        self.assertEqual(query_count_after - query_count_before, 0)

    @override_settings(DEBUG=True)
    def test_prefetch_perms_queryset_query_count(self):
        """
        prefetch_perms with a QuerySet should cause at most 1 extra query
        compared to the list path (the QuerySet evaluation itself).
        The pre-fix code caused 2 extra queries (values_list + iteration);
        after the fix only 1 (a single iteration that populates the cache).
        """
        obj_list = list(Project.objects.filter(pk__in=[p.pk for p in self.projects]).order_by("pk"))

        # --- Measure queryset-based prefetch in isolation ---
        ContentType.objects.clear_cache()

        checker_qs = ObjectPermissionChecker(self.user)
        with CaptureQueriesContext(connection) as qs_ctx:
            checker_qs.prefetch_perms(Project.objects.filter(pk__in=[p.pk for p in self.projects]).order_by("pk"))

        # Count queries that directly SELECT from the Project table (not permission joins)
        project_table = Project._meta.db_table
        qs_project_queries = [q for q in qs_ctx.captured_queries if q["sql"].startswith(f'SELECT "{project_table}"')]

        # --- Measure list-based prefetch in isolation ---
        ContentType.objects.clear_cache()

        checker_list = ObjectPermissionChecker(self.user)
        with CaptureQueriesContext(connection) as list_ctx:
            checker_list.prefetch_perms(obj_list)

        list_project_queries = [
            q for q in list_ctx.captured_queries if q["sql"].startswith(f'SELECT "{project_table}"')
        ]

        # The QuerySet path should issue exactly 1 Project SELECT (the QS eval).
        # The list path issues 0 Project SELECTs (objects already in memory).
        self.assertEqual(
            len(qs_project_queries),
            1,
            f"Expected exactly 1 Project query, got {len(qs_project_queries)}: {qs_project_queries}",
        )
        self.assertEqual(len(list_project_queries), 0)

        # Overall the QS path should have exactly 1 more query than the list path.
        self.assertEqual(len(qs_ctx.captured_queries), len(list_ctx.captured_queries) + 1)

    def test_prefetch_perms_with_queryset_fills_cache_correctly(self):
        """prefetch_perms with QuerySet should fill the cache identically to list input."""
        checker_qs = ObjectPermissionChecker(self.user)
        checker_list = ObjectPermissionChecker(self.user)

        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects]).order_by("pk")
        obj_list = list(qs)

        checker_qs.prefetch_perms(Project.objects.filter(pk__in=[p.pk for p in self.projects]).order_by("pk"))
        checker_list.prefetch_perms(obj_list)

        # Both caches should have the same keys
        self.assertEqual(
            sorted(checker_qs._obj_perms_cache.keys()),
            sorted(checker_list._obj_perms_cache.keys()),
        )

        # Both caches should have the same permission values
        for key in checker_qs._obj_perms_cache:
            self.assertEqual(
                sorted(checker_qs._obj_perms_cache[key]),
                sorted(checker_list._obj_perms_cache[key]),
            )

    def test_prefetch_perms_queryset_permissions_are_correct(self):
        """After prefetch with QuerySet, has_perm should return correct results."""
        checker = ObjectPermissionChecker(self.user)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])

        checker.prefetch_perms(qs)

        self.assertTrue(checker.has_perm("change_project", self.projects[0]))
        self.assertTrue(checker.has_perm("change_project", self.projects[1]))
        self.assertFalse(checker.has_perm("change_project", self.projects[2]))
        self.assertTrue(checker.has_perm("delete_project", self.projects[2]))
        self.assertFalse(checker.has_perm("change_project", self.projects[3]))
        self.assertFalse(checker.has_perm("change_project", self.projects[4]))

    @override_settings(DEBUG=True)
    def test_prefetch_perms_queryset_no_queries_after_prefetch(self):
        """After prefetch_perms, has_perm calls should not hit the DB."""
        checker = ObjectPermissionChecker(self.user)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])
        checker.prefetch_perms(qs)

        query_count = len(connection.queries)
        for project in self.projects:
            checker.has_perm("change_project", project)
            checker.has_perm("delete_project", project)
        self.assertEqual(len(connection.queries), query_count)


class PrefetchPermsWithQuerySetGroupTests(TestCase):
    """Tests for prefetch_perms with QuerySet using group-based permissions."""

    def setUp(self):
        self.group = Group.objects.create(name="testgroup")
        self.projects = [Project.objects.create(name=f"gproject{i}") for i in range(4)]
        assign_perm("change_project", self.group, self.projects[0])
        assign_perm("delete_project", self.group, self.projects[1])

    def test_group_prefetch_with_queryset(self):
        """Group checker should work correctly with QuerySet prefetch."""
        checker = ObjectPermissionChecker(self.group)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])

        checker.prefetch_perms(qs)

        self.assertTrue(checker.has_perm("change_project", self.projects[0]))
        self.assertFalse(checker.has_perm("delete_project", self.projects[0]))
        self.assertFalse(checker.has_perm("change_project", self.projects[1]))
        self.assertTrue(checker.has_perm("delete_project", self.projects[1]))
        self.assertFalse(checker.has_perm("change_project", self.projects[2]))
        self.assertFalse(checker.has_perm("change_project", self.projects[3]))

    @override_settings(DEBUG=True)
    def test_group_prefetch_queryset_no_extra_queries(self):
        """Group prefetch with QuerySet should not cause extra queries on has_perm."""
        checker = ObjectPermissionChecker(self.group)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])
        checker.prefetch_perms(qs)

        query_count = len(connection.queries)
        for project in self.projects:
            checker.has_perm("change_project", project)
        self.assertEqual(len(connection.queries), query_count)

    def test_group_prefetch_cache_has_all_objects(self):
        """Cache should contain entries for all objects in the QuerySet."""
        checker = ObjectPermissionChecker(self.group)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])
        checker.prefetch_perms(qs)

        self.assertEqual(len(checker._obj_perms_cache), len(self.projects))


class PrefetchPermsSuperuserQuerySetTests(TestCase):
    """Tests for prefetch_perms with QuerySet for superusers."""

    def setUp(self):
        self.superuser = User.objects.create(username="superuser", is_active=True, is_superuser=True)
        self.projects = [Project.objects.create(name=f"suproject{i}") for i in range(3)]

    def test_superuser_prefetch_with_queryset(self):
        """Superuser should have all permissions after prefetch with QuerySet."""
        checker = ObjectPermissionChecker(self.superuser)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])

        checker.prefetch_perms(qs)

        for project in self.projects:
            self.assertTrue(checker.has_perm("change_project", project))
            self.assertTrue(checker.has_perm("delete_project", project))
            self.assertTrue(checker.has_perm("add_project", project))

    def test_superuser_prefetch_cache_filled(self):
        """Superuser's cache should have entries for all prefetched objects."""
        checker = ObjectPermissionChecker(self.superuser)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])
        checker.prefetch_perms(qs)

        self.assertEqual(len(checker._obj_perms_cache), len(self.projects))

    @override_settings(DEBUG=True)
    def test_superuser_prefetch_no_queries_after(self):
        """After prefetch, superuser has_perm should not hit DB."""
        checker = ObjectPermissionChecker(self.superuser)
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects])
        checker.prefetch_perms(qs)

        query_count = len(connection.queries)
        for project in self.projects:
            checker.has_perm("change_project", project)
        self.assertEqual(len(connection.queries), query_count)


class PrefetchPermsInactiveUserTests(TestCase):
    """Tests for prefetch_perms with inactive user."""

    def test_inactive_user_returns_empty(self):
        """Inactive user should return empty list from prefetch_perms."""
        user = User.objects.create(username="inactive", is_active=False)
        projects = [Project.objects.create(name=f"inproj{i}") for i in range(2)]
        checker = ObjectPermissionChecker(user)

        result = checker.prefetch_perms(Project.objects.filter(pk__in=[p.pk for p in projects]))

        self.assertEqual(result, [])
        self.assertEqual(len(checker._obj_perms_cache), 0)


class PrefetchPermsGenericRelationQuerySetTests(TestCase):
    """Tests for prefetch_perms with generic relations (Group model) using QuerySet."""

    def setUp(self):
        self.user = User.objects.create(username="genuser", is_active=True)
        self.groups = [Group.objects.create(name=f"gengroup{i}") for i in range(4)]
        self.user.groups.add(*self.groups)
        assign_perm("change_group", self.user, self.groups[0])
        assign_perm("delete_group", self.user, self.groups[1])

    def test_generic_relation_prefetch_with_queryset(self):
        """Prefetch with QuerySet on generic relation model should work correctly."""
        checker = ObjectPermissionChecker(self.user)
        qs = Group.objects.filter(pk__in=[g.pk for g in self.groups])

        checker.prefetch_perms(qs)

        self.assertTrue(checker.has_perm("change_group", self.groups[0]))
        self.assertFalse(checker.has_perm("delete_group", self.groups[0]))
        self.assertFalse(checker.has_perm("change_group", self.groups[1]))
        self.assertTrue(checker.has_perm("delete_group", self.groups[1]))
        self.assertFalse(checker.has_perm("change_group", self.groups[2]))
        self.assertFalse(checker.has_perm("change_group", self.groups[3]))

    def test_generic_relation_cache_size(self):
        """Cache should have an entry for every object in the QuerySet."""
        checker = ObjectPermissionChecker(self.user)
        qs = Group.objects.filter(pk__in=[g.pk for g in self.groups])
        checker.prefetch_perms(qs)

        self.assertEqual(len(checker._obj_perms_cache), len(self.groups))

    @override_settings(DEBUG=True)
    def test_generic_relation_queryset_no_queries_after_prefetch(self):
        """After prefetch, has_perm should not hit DB for generic relations."""
        checker = ObjectPermissionChecker(self.user)
        qs = Group.objects.filter(pk__in=[g.pk for g in self.groups])
        checker.prefetch_perms(qs)

        query_count = len(connection.queries)
        for group in self.groups:
            checker.has_perm("change_group", group)
            checker.has_perm("delete_group", group)
        self.assertEqual(len(connection.queries), query_count)


class PrefetchPermsFilteredQuerySetTests(TestCase):
    """Tests with filtered/sliced QuerySets to ensure correctness."""

    def setUp(self):
        self.user = User.objects.create(username="filteruser", is_active=True)
        self.projects = [Project.objects.create(name=f"fproj{i}") for i in range(6)]
        assign_perm("change_project", self.user, self.projects[0])
        assign_perm("change_project", self.user, self.projects[2])
        assign_perm("change_project", self.user, self.projects[4])

    def test_prefetch_with_filtered_queryset(self):
        """Prefetch should work with a filtered QuerySet (subset of objects)."""
        subset_pks = [self.projects[0].pk, self.projects[1].pk, self.projects[2].pk]
        qs = Project.objects.filter(pk__in=subset_pks)

        checker = ObjectPermissionChecker(self.user)
        checker.prefetch_perms(qs)

        self.assertTrue(checker.has_perm("change_project", self.projects[0]))
        self.assertFalse(checker.has_perm("change_project", self.projects[1]))
        self.assertTrue(checker.has_perm("change_project", self.projects[2]))
        # projects[3] was not prefetched, so checking it will hit DB
        self.assertEqual(len(checker._obj_perms_cache), 3)

    def test_prefetch_with_ordered_queryset(self):
        """Prefetch should work with an ordered QuerySet."""
        qs = Project.objects.filter(pk__in=[p.pk for p in self.projects]).order_by("-pk")

        checker = ObjectPermissionChecker(self.user)
        checker.prefetch_perms(qs)

        self.assertEqual(len(checker._obj_perms_cache), len(self.projects))
        self.assertTrue(checker.has_perm("change_project", self.projects[0]))
        self.assertTrue(checker.has_perm("change_project", self.projects[4]))
        self.assertFalse(checker.has_perm("change_project", self.projects[5]))

    @override_settings(DEBUG=True)
    def test_prefetch_with_large_queryset(self):
        """Prefetch should handle larger QuerySets efficiently."""
        extra_projects = [Project.objects.create(name=f"large{i}") for i in range(20)]
        all_projects = self.projects + extra_projects
        for i, p in enumerate(extra_projects):
            if i % 3 == 0:
                assign_perm("change_project", self.user, p)

        qs = Project.objects.filter(pk__in=[p.pk for p in all_projects])
        checker = ObjectPermissionChecker(self.user)
        checker.prefetch_perms(qs)

        self.assertEqual(len(checker._obj_perms_cache), len(all_projects))

        query_count = len(connection.queries)
        for p in all_projects:
            checker.has_perm("change_project", p)
        self.assertEqual(len(connection.queries), query_count)
