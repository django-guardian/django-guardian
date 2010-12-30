from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import TestCase

from guardian.utils import clean_orphan_obj_perms
from guardian.shortcuts import assign


class OrphanedObjectPermissionsTest(TestCase):

    def setUp(self):
        # Create objects for which we would assing obj perms
        self.target_user1 = User.objects.create(username='user1')
        self.target_group1 = Group.objects.create(name='group1')
        self.target_site1 = Site.objects.create(name='site1')
        self.target_site2 = Site.objects.create(name='site1')

        self.user = User.objects.create(username='user')
        self.group = Group.objects.create(name='group')

    def test_clean_perms(self):

        # assign obj perms
        target_perms = {
            self.target_user1: ["change_user"],
            self.target_group1: ["delete_group"],
            self.target_site1: ["change_site", "delete_site"],
            self.target_site2: ["change_site"],
        }
        obj_perms_count = sum([len(val) for key, val in target_perms.items()])
        for target, perms in target_perms.items():
            target.__old_pk = target.pk # Store pkeys
            for perm in perms:
                assign(perm, self.user, target)

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
            self.target_user1: ["change_user"],
            self.target_group1: ["delete_group"],
            self.target_site1: ["change_site", "delete_site"],
            self.target_site2: ["change_site"],
        }
        for target, perms in target_perms.items():
            target.__old_pk = target.pk # Store pkeys
            for perm in perms:
                assign(perm, self.user, target)

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

