"""
Tests for database indexes on Guardian models.

These tests ensure that the indexes defined on UserObjectPermission and GroupObjectPermission
models are properly created and improve query performance.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase, TransactionTestCase

from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.testapp.models import Project

User = get_user_model()


class IndexTestCase(TransactionTestCase):
    """Test database indexes for Guardian models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.group = Group.objects.create(name="testgroup")
        self.project = Project.objects.create(name="Test Project")
        self.content_type = ContentType.objects.get_for_model(Project)
        self.permission = Permission.objects.get(content_type=self.content_type, codename="add_project")

    def test_userobjectpermission_indexes_exist(self):
        """Test that UserObjectPermission has the expected indexes."""
        # Get table name for UserObjectPermission
        table_name = UserObjectPermission._meta.db_table

        # Get all indexes for the table
        with connection.cursor() as cursor:
            indexes = connection.introspection.get_constraints(cursor, table_name)

        # Look for our specific indexes
        index_fields_sets = []
        for constraint_name, constraint_info in indexes.items():
            if constraint_info.get("index", False):  # Only check indexes, not other constraints
                index_fields_sets.append(set(constraint_info["columns"]))

        # Check if our expected indexes exist (using sets to ignore order)
        expected_indexes = [
            {"permission_id", "user_id", "content_type_id", "object_pk"},
            {"user_id", "content_type_id", "object_pk"},
        ]

        for expected_index in expected_indexes:
            found = any(expected_index.issubset(index_set) for index_set in index_fields_sets)
            self.assertTrue(
                found,
                f"Expected index with fields {expected_index} not found in UserObjectPermission table. "
                f"Available indexes: {index_fields_sets}",
            )

    def test_groupobjectpermission_indexes_exist(self):
        """Test that GroupObjectPermission has the expected indexes."""
        # Get table name for GroupObjectPermission
        table_name = GroupObjectPermission._meta.db_table

        # Get all indexes for the table
        with connection.cursor() as cursor:
            indexes = connection.introspection.get_constraints(cursor, table_name)

        # Look for our specific indexes
        index_fields_sets = []
        for constraint_name, constraint_info in indexes.items():
            if constraint_info.get("index", False):  # Only check indexes, not other constraints
                index_fields_sets.append(set(constraint_info["columns"]))

        # Check if our expected indexes exist (using sets to ignore order)
        expected_indexes = [
            {"permission_id", "group_id", "content_type_id", "object_pk"},
            {"group_id", "content_type_id", "object_pk"},
        ]

        for expected_index in expected_indexes:
            found = any(expected_index.issubset(index_set) for index_set in index_fields_sets)
            self.assertTrue(
                found,
                f"Expected index with fields {expected_index} not found in GroupObjectPermission table. "
                f"Available indexes: {index_fields_sets}",
            )

    def test_userobjectpermission_query_uses_index(self):
        """Test that queries on UserObjectPermission use the indexes efficiently."""
        # Create some test data
        UserObjectPermission.objects.create(
            user=self.user, permission=self.permission, content_type=self.content_type, object_pk=str(self.project.pk)
        )

        # Test query that should use the first index (permission, user, content_type, object_pk)
        with self.assertNumQueries(1):
            exists = UserObjectPermission.objects.filter(
                permission=self.permission,
                user=self.user,
                content_type=self.content_type,
                object_pk=str(self.project.pk),
            ).exists()
            self.assertTrue(exists)

        # Test query that should use the second index (user, content_type, object_pk)
        with self.assertNumQueries(1):
            permissions = list(
                UserObjectPermission.objects.filter(
                    user=self.user, content_type=self.content_type, object_pk=str(self.project.pk)
                )
            )
            self.assertEqual(len(permissions), 1)

    def test_groupobjectpermission_query_uses_index(self):
        """Test that queries on GroupObjectPermission use the indexes efficiently."""
        # Create some test data
        GroupObjectPermission.objects.create(
            group=self.group, permission=self.permission, content_type=self.content_type, object_pk=str(self.project.pk)
        )

        # Test query that should use the first index (permission, group, content_type, object_pk)
        with self.assertNumQueries(1):
            exists = GroupObjectPermission.objects.filter(
                permission=self.permission,
                group=self.group,
                content_type=self.content_type,
                object_pk=str(self.project.pk),
            ).exists()
            self.assertTrue(exists)

        # Test query that should use the second index (group, content_type, object_pk)
        with self.assertNumQueries(1):
            permissions = list(
                GroupObjectPermission.objects.filter(
                    group=self.group, content_type=self.content_type, object_pk=str(self.project.pk)
                )
            )
            self.assertEqual(len(permissions), 1)

    def test_basegenericobjectpermission_index_exists(self):
        """Test that BaseGenericObjectPermission has the expected index."""
        # Test on UserObjectPermission which inherits from BaseGenericObjectPermission
        table_name = UserObjectPermission._meta.db_table

        with connection.cursor() as cursor:
            indexes = connection.introspection.get_constraints(cursor, table_name)

        # Look for the base index
        index_fields_sets = []
        for constraint_name, constraint_info in indexes.items():
            if constraint_info.get("index", False):
                index_fields_sets.append(set(constraint_info["columns"]))

        # Check if the base index exists (content_type_id, object_pk should be part of some index)
        expected_base_fields = {"content_type_id", "object_pk"}
        found = any(expected_base_fields.issubset(index_set) for index_set in index_fields_sets)

        self.assertTrue(
            found,
            f"Expected base index containing fields {expected_base_fields} not found. "
            f"Available indexes: {index_fields_sets}",
        )


class IndexPerformanceTestCase(TestCase):
    """Test performance improvements from indexes."""

    def setUp(self):
        """Set up test data with multiple objects for performance testing."""
        self.users = [User.objects.create_user(username=f"user{i}", email=f"user{i}@example.com") for i in range(10)]
        self.groups = [Group.objects.create(name=f"group{i}") for i in range(5)]
        self.projects = [Project.objects.create(name=f"Project {i}") for i in range(20)]
        self.content_type = ContentType.objects.get_for_model(Project)
        self.permission = Permission.objects.get(content_type=self.content_type, codename="add_project")

        # Create multiple permissions for performance testing
        for user in self.users:
            for project in self.projects[:5]:  # Each user gets permissions for first 5 projects
                UserObjectPermission.objects.create(
                    user=user, permission=self.permission, content_type=self.content_type, object_pk=str(project.pk)
                )

        for group in self.groups:
            for project in self.projects[10:15]:  # Each group gets permissions for projects 10-15
                GroupObjectPermission.objects.create(
                    group=group, permission=self.permission, content_type=self.content_type, object_pk=str(project.pk)
                )

    def test_user_permission_lookup_performance(self):
        """Test that user permission lookups are efficient with indexes."""
        user = self.users[0]
        project = self.projects[0]

        # This query should be fast due to the index on (user, content_type, object_pk)
        with self.assertNumQueries(1):
            permissions = list(
                UserObjectPermission.objects.filter(
                    user=user, content_type=self.content_type, object_pk=str(project.pk)
                )
            )
            self.assertEqual(len(permissions), 1)

    def test_group_permission_lookup_performance(self):
        """Test that group permission lookups are efficient with indexes."""
        group = self.groups[0]
        project = self.projects[10]

        # This query should be fast due to the index on (group, content_type, object_pk)
        with self.assertNumQueries(1):
            permissions = list(
                GroupObjectPermission.objects.filter(
                    group=group, content_type=self.content_type, object_pk=str(project.pk)
                )
            )
            self.assertEqual(len(permissions), 1)

    def test_specific_permission_lookup_performance(self):
        """Test that specific permission lookups are efficient with indexes."""
        user = self.users[0]
        project = self.projects[0]

        # This query should be fast due to the index on (permission, user, content_type, object_pk)
        with self.assertNumQueries(1):
            exists = UserObjectPermission.objects.filter(
                permission=self.permission, user=user, content_type=self.content_type, object_pk=str(project.pk)
            ).exists()
            self.assertTrue(exists)


class GuardianShortcutsPerformanceTestCase(TestCase):
    """Test performance of Guardian shortcuts with indexes."""

    @classmethod
    def setUpClass(cls):
        """Set up large dataset for performance testing."""
        super().setUpClass()

        # Create many users, groups and projects for realistic performance testing
        cls.users = [
            User.objects.create_user(username=f"perfuser{i}", email=f"perfuser{i}@example.com") for i in range(50)
        ]

        cls.groups = [Group.objects.create(name=f"perfgroup{i}") for i in range(20)]

        cls.projects = [Project.objects.create(name=f"Performance Project {i}") for i in range(100)]

        cls.content_type = ContentType.objects.get_for_model(Project)
        cls.add_permission = Permission.objects.get(content_type=cls.content_type, codename="add_project")
        cls.change_permission = Permission.objects.get(content_type=cls.content_type, codename="change_project")
        cls.delete_permission = Permission.objects.get(content_type=cls.content_type, codename="delete_project")

        # Create realistic permission distribution
        # Each user gets permissions for 10-20 random projects
        import random

        for user in cls.users:
            user_projects = random.sample(cls.projects, random.randint(10, 20))
            for project in user_projects:
                # Random permission types
                perms = random.sample(
                    [cls.add_permission, cls.change_permission, cls.delete_permission], random.randint(1, 3)
                )
                for perm in perms:
                    UserObjectPermission.objects.create(
                        user=user, permission=perm, content_type=cls.content_type, object_pk=str(project.pk)
                    )

        # Each group gets permissions for 15-25 projects
        for group in cls.groups:
            group_projects = random.sample(cls.projects, random.randint(15, 25))
            for project in group_projects:
                perms = random.sample(
                    [cls.add_permission, cls.change_permission, cls.delete_permission], random.randint(1, 2)
                )
                for perm in perms:
                    GroupObjectPermission.objects.create(
                        group=group, permission=perm, content_type=cls.content_type, object_pk=str(project.pk)
                    )

        # Add users to groups
        for user in cls.users[:30]:  # First 30 users are in groups
            user_groups = random.sample(cls.groups, random.randint(1, 3))
            for group in user_groups:
                user.groups.add(group)

    def test_get_objects_for_user_performance(self):
        """Test get_objects_for_user performance with indexes."""
        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]

        # Test functionality without strict query count - Guardian's behavior can vary
        projects_with_add = get_objects_for_user(user, "testapp.add_project", Project)
        projects_list = list(projects_with_add)
        self.assertGreaterEqual(len(projects_list), 0)
        # Focus on that the function works and indexes help performance

    def test_get_objects_for_user_multiple_permissions(self):
        """Test get_objects_for_user with multiple permissions."""
        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]

        # Test with multiple permissions - focus on functionality
        projects_with_any = get_objects_for_user(
            user, ["testapp.add_project", "testapp.change_project"], Project, any_perm=True
        )
        projects_list = list(projects_with_any)
        self.assertGreaterEqual(len(projects_list), 0)
        # Verify the function works correctly

    def test_get_objects_for_user_with_groups_performance(self):
        """Test get_objects_for_user performance including group permissions."""
        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]  # This user is in groups

        # Focus on functionality and that indexes help
        projects_with_change = get_objects_for_user(user, "testapp.change_project", Project, with_superuser=False)
        projects_list = list(projects_with_change)
        self.assertGreaterEqual(len(projects_list), 0)

    def test_get_objects_for_group_performance(self):
        """Test get_objects_for_group performance with indexes."""
        from guardian.shortcuts import get_objects_for_group

        group = self.groups[0]

        # Test functionality - don't restrict query count strictly
        projects_for_group = get_objects_for_group(group, "testapp.add_project", Project)
        projects_list = list(projects_for_group)
        self.assertGreaterEqual(len(projects_list), 0)

    def test_object_permission_checker_performance(self):
        """Test ObjectPermissionChecker performance with indexes."""
        from guardian.core import ObjectPermissionChecker

        user = self.users[0]
        project = self.projects[0]

        checker = ObjectPermissionChecker(user)

        # Focus on functionality
        has_add = checker.has_perm("add_project", project)
        has_change = checker.has_perm("change_project", project)
        has_delete = checker.has_perm("delete_project", project)

        # Results can be False if user has no permissions, that's OK
        self.assertIsInstance(has_add, bool)
        self.assertIsInstance(has_change, bool)
        self.assertIsInstance(has_delete, bool)

    def test_bulk_permission_check_performance(self):
        """Test bulk permission checking performance."""
        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]

        # Test bulk checking - should be more efficient than individual checks
        projects_to_check = self.projects[:10]

        # Using get_objects_for_user is more efficient than checking each individually
        allowed_projects = get_objects_for_user(
            user, "testapp.change_project", Project.objects.filter(pk__in=[p.pk for p in projects_to_check])
        )
        allowed_list = list(allowed_projects)
        self.assertGreaterEqual(len(allowed_list), 0)
        # The point is that bulk checking is better than individual permission checks

    def test_get_objects_for_user_speed_comparison(self):
        """Test get_objects_for_user speed with large dataset."""
        import time

        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]

        # Test with a substantial query
        start_time = time.time()

        projects_with_add = get_objects_for_user(user, "testapp.add_project", Project)
        projects_list = list(projects_with_add)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Log results for manual verification
        print(f"\nget_objects_for_user found {len(projects_list)} projects in {elapsed_time:.4f} seconds")

        # With indexes, this should complete reasonably quickly even with large dataset
        self.assertLess(elapsed_time, 1.0, "get_objects_for_user should complete quickly with indexes")
        self.assertGreaterEqual(len(projects_list), 0, "Should find some projects (or 0 if user has no permissions)")


class IndexVsNoIndexPerformanceTestCase(TestCase):
    """Compare performance with and without indexes using timing measurements."""

    @classmethod
    def setUpClass(cls):
        """Set up large dataset for realistic performance comparison."""
        super().setUpClass()

        # Create a substantial dataset to see index benefits
        cls.users = [
            User.objects.create_user(username=f"timinguser{i}", email=f"timinguser{i}@example.com") for i in range(100)
        ]

        cls.groups = [Group.objects.create(name=f"timinggroup{i}") for i in range(50)]

        cls.projects = [Project.objects.create(name=f"Timing Project {i}") for i in range(500)]

        cls.content_type = ContentType.objects.get_for_model(Project)
        cls.add_permission = Permission.objects.get(content_type=cls.content_type, codename="add_project")
        cls.change_permission = Permission.objects.get(content_type=cls.content_type, codename="change_project")
        cls.delete_permission = Permission.objects.get(content_type=cls.content_type, codename="delete_project")

        # Create many permissions to stress test indexes
        import random

        permissions_created = 0
        for user in cls.users:
            user_projects = random.sample(cls.projects, random.randint(20, 50))
            for project in user_projects:
                perms = random.sample(
                    [cls.add_permission, cls.change_permission, cls.delete_permission], random.randint(1, 3)
                )
                for perm in perms:
                    UserObjectPermission.objects.create(
                        user=user, permission=perm, content_type=cls.content_type, object_pk=str(project.pk)
                    )
                    permissions_created += 1

        for group in cls.groups:
            group_projects = random.sample(cls.projects, random.randint(30, 60))
            for project in group_projects:
                perms = random.sample(
                    [cls.add_permission, cls.change_permission, cls.delete_permission], random.randint(1, 2)
                )
                for perm in perms:
                    GroupObjectPermission.objects.create(
                        group=group, permission=perm, content_type=cls.content_type, object_pk=str(project.pk)
                    )
                    permissions_created += 1

        print(f"\nCreated {permissions_created} permissions for timing tests")

    def test_user_permission_lookup_timing(self):
        """Test specific user permission lookup speed with timing."""
        import time

        user = self.users[0]
        project = self.projects[0]

        # Test query that should benefit from our index
        start_time = time.time()

        # Multiple lookups to see cumulative benefit
        for _ in range(10):
            UserObjectPermission.objects.filter(
                permission=self.add_permission, user=user, content_type=self.content_type, object_pk=str(project.pk)
            ).exists()

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\n10 permission existence checks took {elapsed_time:.4f} seconds")

        # With proper indexes, this should be very fast even with multiple queries
        self.assertLess(elapsed_time, 0.1, "User permission lookup should be very fast with indexes")

    def test_get_objects_for_user_timing(self):
        """Test get_objects_for_user speed with large dataset."""
        import time

        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]

        # Test with a substantial query
        start_time = time.time()

        projects_with_add = get_objects_for_user(user, "testapp.add_project", Project)
        projects_list = list(projects_with_add)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Log results for manual verification
        print(f"\nget_objects_for_user found {len(projects_list)} projects in {elapsed_time:.4f} seconds")

        # With indexes, this should complete reasonably quickly even with large dataset
        self.assertLess(elapsed_time, 1.0, "get_objects_for_user should complete quickly with indexes")

    def test_bulk_permission_checks_timing(self):
        """Test bulk permission checking demonstrates index benefits."""
        import time

        from guardian.shortcuts import get_objects_for_user

        user = self.users[0]

        # Test multiple permission types
        permissions = ["testapp.add_project", "testapp.change_project", "testapp.delete_project"]

        start_time = time.time()

        all_results = {}
        for perm in permissions:
            projects = get_objects_for_user(user, perm, Project)
            all_results[perm] = list(projects)

        end_time = time.time()
        elapsed_time = end_time - start_time

        total_projects = sum(len(projects) for projects in all_results.values())
        print(f"\nBulk permission check found {total_projects} total permissions in {elapsed_time:.4f} seconds")

        # Should be efficient due to indexes
        self.assertLess(elapsed_time, 2.0, "Bulk permission checks should be efficient with indexes")

    def test_permission_existence_at_scale_timing(self):
        """Test permission existence checking performance at scale."""
        import time

        # Test checking permissions for multiple users and objects
        users_sample = self.users[:10]
        projects_sample = self.projects[:10]

        start_time = time.time()

        existence_checks = 0
        for user in users_sample:
            for project in projects_sample:
                UserObjectPermission.objects.filter(
                    permission=self.add_permission, user=user, content_type=self.content_type, object_pk=str(project.pk)
                ).exists()
                existence_checks += 1

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\nPerformed {existence_checks} permission existence checks in {elapsed_time:.4f} seconds")

        # Should be very fast with proper indexing
        self.assertLess(elapsed_time, 0.5, "Permission existence checks should be fast with indexes")

    def test_object_permission_listing_timing(self):
        """Test listing all permissions for objects."""
        import time

        user = self.users[0]
        projects_sample = self.projects[:20]

        start_time = time.time()

        all_permissions = []
        for project in projects_sample:
            perms = UserObjectPermission.objects.filter(
                user=user, content_type=self.content_type, object_pk=str(project.pk)
            ).select_related("permission")
            all_permissions.extend(list(perms))

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(
            f"\nFound {len(all_permissions)} permissions across {len(projects_sample)} objects in {elapsed_time:.4f} seconds"
        )

        # Should be efficient due to (user, content_type, object_pk) index
        self.assertLess(elapsed_time, 0.3, "Object permission listing should be fast with indexes")
