#!/usr/bin/env python
"""
This benchmark package should be treated as work-in-progress, not a production
ready benchmarking solution for django-guardian.
"""
import datetime
import os
import random
import string
import sys

abspath = lambda *p: os.path.abspath(os.path.join(*p))

THIS_DIR = abspath(os.path.dirname(__file__))
ROOT_DIR = abspath(THIS_DIR, '..')

# so the preferred guardian module is one within this repo and
# not system-wide
sys.path.insert(0, ROOT_DIR)

os.environ["DJANGO_SETTINGS_MODULE"] = 'benchmarks.settings'

import django
django.setup()

from benchmarks import settings
from guardian.shortcuts import assign_perm
from django.core.exceptions import ImproperlyConfigured
from utils import show_settings
from django.contrib.auth.models import User, Group
from django.utils.termcolors import colorize
from benchmarks.models import TestModel
from benchmarks.models import TestDirectModel
from guardian.models import UserObjectPermission
from django.contrib.contenttypes.models import ContentType

USERS_COUNT = 50
OBJECTS_COUNT = 100
OBJECTS_WIHT_PERMS_COUNT = 100


def random_string(length=25, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for i in range(length))


class Call:

    def __init__(self, args, kwargs, start=None, finish=None):
        self.args = args
        self.kwargs = kwargs
        self.start = start
        self.finish = finish

    def delta(self):
        return self.finish - self.start


class Timed:

    def __init__(self, action=None):
        self.action = action

    def __call__(self, func):

        if not hasattr(func, 'calls'):
            func.calls = []

        def wrapper(*args, **kwargs):
            if self.action:
                print(" -> [%s]" % self.action)
            start = datetime.datetime.now()
            call = Call(list(args), dict(kwargs), start)
            try:
                return func(*args, **kwargs)
            finally:
                call.finish = datetime.datetime.now()
                func.calls.append(call)
                if self.action:
                    print(" -> [{}] Done (Total time: {})".format(self.action,
                                                              call.delta()))
        return wrapper


class Benchmark:

    def __init__(self, name, users_count, objects_count,
                 objects_with_perms_count, model, subquery):
        self.name = name
        self.users_count = users_count
        self.objects_count = objects_count
        self.objects_with_perms_count = objects_with_perms_count
        self.subquery = subquery
        self.Model = model
        self.perm = 'add_%s' % model._meta.model_name

    def info(self, msg):
        print(colorize(msg + '\n', fg='green'))

    def prepare_db(self):
        from django.core.management import call_command
        call_command('makemigrations', interactive=False)
        call_command('migrate', interactive=False)

        for model in [User, Group, self.Model]:
            model.objects.all().delete()

    @Timed("Creating users")
    def create_users(self):
        User.objects.bulk_create(User(id=x, username=random_string().capitalize())
                                 for x in range(self.users_count))

    @Timed("Creating objects")
    def create_objects(self):
        Model = self.Model
        Model.objects.bulk_create(Model(id=x, name=random_string(20))
                                  for x in range(self.objects_count))

    @Timed("Grant permissions")
    def grant_perms(self):
        ids = range(1, self.objects_count)
        for user in User.objects.iterator():
            for x in xrange(self.objects_with_perms_count):
                obj = self.Model.objects.get(id=random.choice(ids))
                self.grant_perm(user, obj, self.perm)

    def grant_perm(self, user, obj, perm):
        assign_perm(perm, user, obj)

    @Timed("Check permissions")
    def check_perms(self):
        ids = range(1, self.objects_count)
        for user in User.objects.iterator():
            for x in xrange(self.objects_with_perms_count):
                obj = self.Model.objects.get(id=random.choice(ids))
                self.check_perm(user, obj, self.perm)

    @Timed("Get objects")
    def get_objects(self):
        ctype = ContentType.objects.get_for_model(self.Model)
        ids = range(1, self.users_count)
        for user in User.objects.iterator():
            for x in xrange(self.objects_with_perms_count):
                filters = {'user': random.choice(ids),
                           'permission__codename__in': [self.perm],
                           'content_type': ctype
                           }
                qs = UserObjectPermission.objects.filter(**filters).all()
                if not self.subquery:
                    qs = [v.object_pk for v in qs]
                list(self.Model.objects.filter(id__in=qs))

    def check_perm(self, user, obj, perm):
        user.has_perm(perm, obj)

    @Timed("Benchmark")
    def main(self):
        self.info('=' * 80)
        self.info(self.name.center(80))
        self.info('=' * 80)
        self.prepare_db()
        self.create_users()
        self.create_objects()
        self.grant_perms()
        self.check_perms()
        if not isinstance(self.Model, TestModel):
            self.get_objects()


def main():
    show_settings(settings, 'benchmarks')
    glob = [USERS_COUNT, OBJECTS_COUNT, OBJECTS_WIHT_PERMS_COUNT]
    Benchmark('Direct relations benchmark with subqueries', *glob,
              model=TestDirectModel, subquery=True).main()

    Benchmark('Direct relations benchmark without subqueries', *glob,
              model=TestDirectModel, subquery=False).main()

    Benchmark('Generic relations benchmark without subqueries', *glob,
              model=TestModel, subquery=False).main()

if __name__ == '__main__':
    main()
