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
    >>> UserObjectPermission.objects.assign_perm('change_group', user=jack, obj=admins)
    <UserObjectPermission: admins | jack | change_group>
    >>> jack.has_perm('change_group', admins)
    True

Of course our agent jack here would not be able to *change_group* globally::

    >>> jack.has_perm('change_group')
    False

Admin integration
-----------------

There two ways to include django-guradian object level admin support for your models. One is relatively straightforward 
and consists of replacing ``admin.ModelAdmin`` with ``GuardedModelAdmin`` for those models which should have object 
permissions support within admin panel:

.. code-block:: python

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

The other consists of sanely monkeypatching. This has the great benefit that existing Django models, third party apps,
your models and future models - the entire Django site automatically gets object level permission support in the Admin:

.. code-block:: python

	import logging
	logger = logging.getLogger(__name__)
	# be nice and tell you are patching
	logger.info("Patching 'admin.ModelAdmin = GuardedModelAdmin': replace 'admin.ModelAdmin' with 'GuardedModelAdmin' "
				"which provides an ability to edit object level permissions.")
	# confirm signature of code we are patching and warn if it has changed
	if not '3c43401f585ae4a368c901e96f233981' == \
			hashlib.md5(inspect.getsource(admin.ModelAdmin)).hexdigest():
		logger.warn("md5 signature of 'admin.ModelAdmin' does not match Django 1.5. There is a slight change patch "
					"might be broken so please compare and update this monkeypatch.")
	admin.ModelAdmin = GuardedModelAdmin # apply the patch

.. [1] Great paper about this feature is available at `djangoadvent articles <https://github.com/djangoadvent/djangoadvent-articles/blob/master/1.2/06_object-permissions.rst>`_.

.. _Django: http://www.djangoproject.org/

