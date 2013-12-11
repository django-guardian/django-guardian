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

If ``ANONYMOUS_USER_ID`` is set to ``None``, anonymous user object permissions
are disabled. You may need to choose this option if creating a ``User`` object
to represent anonymous users would be problematic in your environment.

We can change id to whatever we like. Project should be now ready to use object
permissions.
 

Optional settings
=================

In addition to required ``ANONYMOUS_USER_ID`` setting, guardian has following,
optional configuration variables:


.. setting:: GUARDIAN_RAISE_403

GUARDIAN_RAISE_403
------------------

.. versionadded:: 1.0.4

If set to ``True``, guardian would raise
``django.core.exceptions.PermissionDenied`` error instead of returning empty
``django.http.HttpResponseForbidden``.

.. warning::

 Remember that you cannot use both :setting:`GUARDIAN_RENDER_403` **AND**
 :setting:`GUARDIAN_RAISE_403` - if both are set to ``True``,
 ``django.core.exceptions.ImproperlyConfigured`` would be raised.



.. setting:: GUARDIAN_RENDER_403

GUARDIAN_RENDER_403
-------------------

.. versionadded:: 1.0.4

If set to ``True``, guardian would try to render 403 response rather than
return contentless ``django.http.HttpResponseForbidden``. Would use template
pointed by :setting:`GUARDIAN_TEMPLATE_403` to do that. Default is ``False``.

.. warning::

 Remember that you cannot use both :setting:`GUARDIAN_RENDER_403` **AND**
 :setting:`GUARDIAN_RAISE_403` - if both are set to ``True``,
 ``django.core.exceptions.ImproperlyConfigured`` would be raised.


.. setting:: GUARDIAN_TEMPLATE_403

GUARDIAN_TEMPLATE_403
---------------------

.. versionadded:: 1.0.4

Tells parts of guardian what template to use for responses with status code
``403`` (i.e. :ref:`api-decorators-permission_required`). Defaults to
``403.html``.


.. setting:: ANONYMOUS_DEFAULT_USERNAME_VALUE

ANONYMOUS_DEFAULT_USERNAME_VALUE
--------------------------------

.. versionadded:: 1.1

Due to changes introduced by Django 1.5 user model can have differently named
``username`` field (it can be removed too, but ``guardian`` currently depends
on it). After ``syncdb`` command we create anonymous user for convenience,
however it might be necessary to set this configuration in order to set proper
value at ``username`` field.

.. seealso:: https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#substituting-a-custom-user-model

