from django.test import TestCase
from django.template import Template, Context, TemplateSyntaxError
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.flatpages.models import FlatPage

from guardian.exceptions import NotUserNorGroup
from guardian.models import UserObjectPermission, GroupObjectPermission

def render(template, context):
    """
    Returns rendered ``template`` with ``context``, which are given as string
    and dict respectively.
    """
    t = Template(template)
    return t.render(Context(context))

class GetObjPermsTagTest(TestCase):
    fixtures = ['tests.json']

    def setUp(self):
        self.flatpage = FlatPage.objects.create(title='Any page', url='/any/')
        self.user = User.objects.get(username='jack')
        self.group = Group.objects.get(name='jackGroup')
        UserObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()

    def test_wrong_formats(self):
        wrong_formats = (
            #'{% get_obj_perms user for flatpage as obj_perms %}', # no quotes
            '{% get_obj_perms user for flatpage as \'obj_perms" %}', # wrong quotes
            '{% get_obj_perms user for flatpage as \'obj_perms" %}', # wrong quotes
            '{% get_obj_perms user for flatpage as obj_perms" %}', # wrong quotes
            '{% get_obj_perms user for flatpage as obj_perms\' %}', # wrong quotes
            '{% get_obj_perms user for flatpage as %}', # no context_var
            '{% get_obj_perms for flatpage as "obj_perms" %}', # no user/group
            '{% get_obj_perms user flatpage as "obj_perms" %}', # no "for" bit
            '{% get_obj_perms user for flatpage "obj_perms" %}', # no "as" bit
            '{% get_obj_perms user for as "obj_perms" %}', # no object
        )

        context = {'user': User.get_anonymous(), 'flatpage': self.flatpage}
        for wrong in wrong_formats:
            fullwrong = '{% load guardian_tags %}' + wrong
            try:
                render(fullwrong, context)
                self.fail("Used wrong get_obj_perms tag format: \n\n\t%s\n\n "
                    "but TemplateSyntaxError have not been raised" % wrong)
            except TemplateSyntaxError:
                pass

    def test_anonymous_user(self):
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for flatpage as "obj_perms" %}{{ perms }}',
        ))
        context = {'user': AnonymousUser(), 'flatpage': self.flatpage}
        anon_output = render(template, context)
        context = {'user': User.get_anonymous(), 'flatpage': self.flatpage}
        real_anon_user_output = render(template, context)
        self.assertEqual(anon_output, real_anon_user_output)

    def test_wrong_user_or_group(self):
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms some_obj for flatpage as "obj_perms" %}',
        ))
        context = {'some_obj': FlatPage(), 'flatpage': self.flatpage}
        self.assertRaises(NotUserNorGroup, render, template, context)

    def test_superuser(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for flatpage as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'user': user, 'flatpage': self.flatpage}
        output = render(template, context)

        for perm in ('add_flatpage', 'change_flatpage', 'delete_flatpage'):
            self.assertTrue(perm in output)

    def test_user(self):
        UserObjectPermission.objects.assign("change_flatpage", self.user,
            self.flatpage)
        GroupObjectPermission.objects.assign("delete_flatpage", self.group,
            self.flatpage)

        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for flatpage as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'user': self.user, 'flatpage': self.flatpage}
        output = render(template, context)

        self.assertEqual(output, 'change_flatpage delete_flatpage')

    def test_group(self):
        GroupObjectPermission.objects.assign("delete_flatpage", self.group,
            self.flatpage)

        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms group for flatpage as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'group': self.group, 'flatpage': self.flatpage}
        output = render(template, context)

        self.assertEqual(output, 'delete_flatpage')

