===============
django-guardian
===============

.. image:: https://secure.travis-ci.org/lukaszb/django-guardian.png?branch=master
  :target: http://travis-ci.org/lukaszb/django-guardian

.. image:: https://coveralls.io/repos/lukaszb/django-guardian/badge.png?branch=master
   :target: https://coveralls.io/r/lukaszb/django-guardian/

.. image:: https://pypip.in/v/django-guardian/badge.png
  :target: https://crate.io/packages/django-guardian/

.. image:: https://pypip.in/d/django-guardian/badge.png
  :target: https://crate.io/packages/django-guardian/


``django-guardian`` is implementation of per object permissions [1]_ as 
authorization backend which is supported since Django_ 1.2. It won't
work with older Django_ releases.

Documentation
-------------

Online documentation is available at http://django-guardian.rtfd.org/.

Installation
------------

To install ``django-guardian`` simply run::

    pip install django-guardian

Configuration
-------------

We need to hook ``django-guardian`` into our project.

1. Put ``guardian`` into your ``INSTALLED_APPS`` at settings module::

      INSTALLED_APPS = (
         ...
         'guardian',
      )
   
2. Add extra authorization backend::

      AUTHENTICATION_BACKENDS = (
          'django.contrib.auth.backends.ModelBackend', # default
          'guardian.backends.ObjectPermissionBackend',
      )

3. Configure anonymous user ID ::

     ANONYMOUS_USER_ID = -1

         
Usage
-----

After installation and project hooks we can finally use object permissions
with Django_.

Lets start really quickly::

    >>> jack = User.objects.create_user('jack', 'jack@example.com', 'topsecretagentjack')
    >>> admins = Group.objects.create(name='admins')
    >>> jack.has_perm('change_group', admins)
    False
    >>> UserObjectPermission.objects.assign_perm('change_group', user=jack, obj=admins)
    <UserObjectPermission: admins | jack | change_group>
    >>> jack.has_perm('change_group', admins)
    True

Of course our agent jack here would not be able to *change_group* globally::

    >>> jack.has_perm('change_group')
    False

Admin integration
-----------------

Replace ``admin.ModelAdmin`` with ``GuardedModelAdmin`` for those models
which should have object permissions support within admin panel.

For example::

    from django.contrib import admin
    from myapp.models import Author
    from guardian.admin import GuardedModelAdmin

    # Old way:
    #class AuthorAdmin(admin.ModelAdmin):
    #    pass

    # With object permissions support
    class AuthorAdmin(GuardedModelAdmin):
        pass

    admin.site.register(Author, AuthorAdmin)


.. [1] Great paper about this feature is available at `djangoadvent articles <https://github.com/djangoadvent/djangoadvent-articles/blob/master/1.2/06_object-permissions.rst>`_.

.. _Django: http://www.djangoproject.com/

