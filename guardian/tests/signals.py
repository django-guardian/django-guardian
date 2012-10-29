""" test for custom signals
"""
import mock

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch.dispatcher import receiver
from guardian.core import ObjectPermissionChecker

from guardian.shortcuts import get_perm_codenames_for_model
from guardian.signals import get_perms
from guardian.tests.core_test import ObjectPermissionTestCase
from guardian.tests.tags_test import render


@receiver(get_perms, sender=User, weak=False,
          dispatch_uid='guardian.test.signals.signal_get_perms_user')
def signal_get_perms_user(sender, user, obj, **kwargs):
    """ return the permissions of @user on object @obj
    """
    if obj.username == 'jack':
        if user.username in ('mum', 'dad'):
            return get_perm_codenames_for_model(User)
        if user.username == 'bob':
            return ['another_custom_perm', ]
    return []


class GetPermsSignalTest(ObjectPermissionTestCase):

    def setUp(self):
        super(GetPermsSignalTest, self).setUp()

        self.mum, created = User.objects.get_or_create(username='mum')
        self.dad, created = User.objects.get_or_create(username='dad')
        self.bob, created = User.objects.get_or_create(username='bob')

        Permission.objects.create(
            name='Can do something', codename='a_custom_perm',
            content_type=ContentType.objects.get_for_model(User)
        )
        Permission.objects.create(
            name='Can do something else', codename='another_custom_perm',
            content_type=ContentType.objects.get_for_model(User)
        )

    def test_has_perm(self):
        self.assertTrue(self.mum.has_perm('a_custom_perm', self.user))
        self.assertTrue(self.dad.has_perm('a_custom_perm', self.user))
        self.assertFalse(self.bob.has_perm('a_custom_perm', self.user))
        self.assertTrue(self.bob.has_perm('another_custom_perm', self.user))

    def test_tags(self):
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms someone for jack as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'jack': self.user, 'someone': self.mum}
        output = render(template, context)

        self.assertEqual(
            set(output.split(' ')),
            set(get_perm_codenames_for_model(User)))

        context = {'jack': self.user, 'someone': self.bob}
        output = render(template, context)

        self.assertEqual(
            set(output.split(' ')),
            set(('another_custom_perm', )))

    def test_cache(self):
        checker = ObjectPermissionChecker(self.mum)

        with mock.patch('guardian.tests.signals.signal_get_perms_user', return_value=[], autospec=True) as mocked_handler:
            get_perms.connect(mocked_handler, sender=User,
                              dispatch_uid='test_cache_mocked_handler')

        checker.has_perm('a_custom_perm', self.user)
        checker.has_perm('another_custom_perm', self.user)

        self.assertEqual(mocked_handler.call_count, 1)
