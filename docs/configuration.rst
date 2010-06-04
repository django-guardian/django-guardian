.. _configuration:

Configuration
=============

After :ref:`installation <installation>` we can prepare our project for object
permissions handling. In a settings module we need to add guardian to
``INSTALLED_APPS``::

   INSTALLED_APPS = (
       # ...
       'guardian',
   )

and hook guardian's authentication backend::

   AUTHENTICATION_BACKENDS = (
       'django.contrib.auth.backends.ModelBackend', # this is default
       'guardian.backends.ObjectPermissionBackend',
   )

As ``django-guardian`` supports anonymous user's object permissions we also
need to add following to our settings module::

   ANONYMOUS_USER_ID = -1

.. note::
   Once project is configured to work with ``django-guardian``, calling
   ``syncdb`` management command would create ``User`` instance for
   anonymous user support (with name of ``AnonymousUser``).

We can change id to whatever we like. Project should be now ready to use object
permissions.
 
