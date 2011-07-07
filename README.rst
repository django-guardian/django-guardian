===============
django-guardian
===============

``django-guardian`` is implementation of per object permissions [1]_ as 
authorization backend which is supported since Django_ 1.2. It won't
work with older Django_ releases.

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
         
Usage
-----

After installation and project hooks we can finally use object permissions
with Django_.

Lets start really quickly::

    >>> jack = User.objects.create_user('jack', 'jack@example.com', 'topsecretagentjack')
    >>> admins = Group.objects.create(name='admins')
    >>> jack.has_perm('change_group', admins)
    False
    >>> UserObjectPermission.objects.assign('change_group', user=jack, obj=admins)
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

Documentation
-------------

There is an online documentation available at
http://packages.python.org/django-guardian/.


.. [1] Great paper about this feature is available at 
   http://djangoadvent.com/1.2/object-permissions/.

.. _Django: http://www.djangoproject.org/

