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
 

Optional settings
=================

In addition to requried ``ANONYMOUS_USER_ID`` setting, guardian has following,
optional configuration variables:


.. setting:: GUARDIAN_RENDER_403

* ``GUARDIAN_RENDER_403``

  If set to ``True``, guardian would try to render 403 response rather than
  return contentless ``django.http.HttpResponseForbidden``. Would use template
  pointed by :setting:`GUARDIAN_TEMPLATE_403` to do that. Default is ``False``.


.. setting:: GUARDIAN_TEMPLATE_403

* ``GUARDIAN_TEMPLATE_403``

    Tells parts of guardian what template to use for responses with status code
    ``403`` (i.e. :ref:`api-decorators-permission_required`). Defaults to
    ``403.html``.

