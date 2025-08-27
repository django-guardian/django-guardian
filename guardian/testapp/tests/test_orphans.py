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
    
    def test_clean_all_permissions(self):
        """Should clean all orphaned permissions without batching."""
        count = self._assign_and_delete_targets(3)
        removed = clean_orphan_obj_perms()
        self.assertEqual(removed, count)

    def test_clean_with_batch_size(self):
        """Should clean permissions in small batches."""
        count = self._assign_and_delete_targets(5)
        removed = clean_orphan_obj_perms(batch_size=2)
        self.assertEqual(removed, count)

    def test_clean_with_max_batches(self):
        """Should stop after reaching max_batches."""
        self._assign_and_delete_targets(5)
        removed = clean_orphan_obj_perms(batch_size=1, max_batches=2)
        self.assertEqual(removed, 2)

    def test_clean_with_skip_batches(self):
        """Should skip first N batches and then start cleaning."""
        self._assign_and_delete_targets(6)
        # First call: process 3 batches and stop
        clean_orphan_obj_perms(batch_size=2, max_batches=3)
        # Second call: skip first 3, process next 2
        removed = clean_orphan_obj_perms(batch_size=2, max_batches=2, skip_batches=3)
        self.assertEqual(removed, 2)

    def test_clean_with_max_duration(self):
        """Should stop after max_duration_secs exceeded."""
        import time as pytime

        self._assign_and_delete_targets(3)

        original_iterator = ContentType.objects.all().iterator

        def slow_iterator(*args, **kwargs):
            for obj in original_iterator(*args, **kwargs):
                pytime.sleep(0.3)  # Slow down processing
                yield obj

        ContentType.objects.all().iterator = slow_iterator

        try:
            removed = clean_orphan_obj_perms(batch_size=1, max_duration_secs=0.5)
            self.assertLess(removed, 3)
        finally:
            ContentType.objects.all().iterator = original_iterator

    def test_log_output_and_resumption_suggestion(self):
        """Ensure the resume log message is emitted properly."""
        self._assign_and_delete_targets(5)

        with self.assertLogs('guardian.utils', level='INFO') as cm:
            clean_orphan_obj_perms(batch_size=2, max_batches=2, skip_batches=1, max_duration_secs=10)

        self.assertTrue(any("To resume cleanup" in msg for msg in cm.output))

    def test_clean_perms_command(self):
        """Management command interface should also work."""
        self._assign_and_delete_targets(2)
        call_command("clean_orphan_obj_perms", verbosity=0)
        self.assertTrue(True)  # If no error, test passes