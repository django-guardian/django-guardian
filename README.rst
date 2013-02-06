===============
django-guardian
===============

.. image:: https://secure.travis-ci.org/lukaszb/django-guardian.png?branch=master
  :target: http://travis-ci.org/lukaszb/django-guardian


``django-guardian`` is implementation of per object permissions [1]_ as 
authorization backend which is supported since Django_ 1.2. It won't
work with older Django_ releases.

Documentation
-------------

Online documentation is available at

http://packages.python.org/django-guardian/ or http://django-guardian.rtfd.org/

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

Using signals
-------------

If you need to specify permissions based on some very specific logic, you
can use signals to make your life easier.

Suppose for example that you have a model such this::

    class MyModel(models.Model):
        owner = models.ForeignKey(User)
        # other stuff

and that the ``owner`` of an instance of ``MyModel`` has special permissions
of his/her instances. Instead of updating the permissions every time the ``owner``
changes, you can just register a signal such this::

    from guardian.signals import get_perms
    from guardian.shortcuts import get_perm_codenames_for_model
    
    @receiver(get_perms, sender=MyModel,
              dispatch_uid='myapp.signal_get_perms_mymodel')
    def signal_get_perms_mymodel(sender, user, obj, **kwargs):
        if user == obj.owner:
            return get_perm_codenames_for_model(MyModel)
        return []

All the permissions returned by such handlers will be added to the user permissions,
and will be cached for future calls.


.. [1] Great paper about this feature is available at `djangoadvent articles <https://github.com/djangoadvent/djangoadvent-articles/blob/master/1.2/06_object-permissions.rst>`_.

.. _Django: http://www.djangoproject.org/
