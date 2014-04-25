.. _configuration:

Configuration
=============

After :ref:`installation <installation>` we can prepare our project for object
permissions handling. In a settings module (generally a settings.py file) we need to add guardian to:
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

Since ``django-guardian`` supports object permissions for anonymous users, we also
need to add following to our settings module::

   ANONYMOUS_USER_ID = -1

.. note::
   Once your project is configured to work with ``django-guardian``, calling
   the ``syncdb`` management command will create a ``User`` instance for
   anonymous user support with the name ``AnonymousUser``.

If ``ANONYMOUS_USER_ID`` is set to ``None``, anonymous user object permissions
are disabled. You may need to choose this option if creating a ``User`` object
to represent anonymous users would be problematic in your environment.

We can change the Anonymous User id to whatever we like. Your project should be now ready to use object
permissions.
 

Optional settings
=================

In addition to the required ``ANONYMOUS_USER_ID`` setting, guardian has the following
optional configuration variables:


.. setting:: GUARDIAN_RAISE_403

GUARDIAN_RAISE_403
------------------

.. versionadded:: 1.0.4

If set to ``True``, guardian would raise
``django.core.exceptions.PermissionDenied`` error instead of returning an empty
``django.http.HttpResponseForbidden``.

.. warning::

 Remember that you cannot use both :setting:`GUARDIAN_RENDER_403` **AND**
 :setting:`GUARDIAN_RAISE_403` - if both are set to ``True``,
 ``django.core.exceptions.ImproperlyConfigured`` WILL be raised.



.. setting:: GUARDIAN_RENDER_403

GUARDIAN_RENDER_403
-------------------

.. versionadded:: 1.0.4

If set to ``True``, guardian will try to render a 403 response rather than
return a contentless ``django.http.HttpResponseForbidden``. It will use the template
pointed to by :setting:`GUARDIAN_TEMPLATE_403`. The default setting is ``False``.

.. warning::

 Remember that you cannot use both :setting:`GUARDIAN_RENDER_403` **AND**
 :setting:`GUARDIAN_RAISE_403` - if both are set to ``True``,
 ``django.core.exceptions.ImproperlyConfigured`` WILL be raised.


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

Due to changes introduced by Django 1.5, the user model can have a differently named
``username`` field. The ``username`` field can also be removed but ``guardian`` currently depends
on the ``username`` field: after running a ``syncdb`` command we create the anonymous user for convenience;
however, it might be necessary to set this configuration in order to set the proper
value to the ``username`` field.

.. seealso:: https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#substituting-a-custom-user-model


.. setting:: GUARDIAN_GET_INIT_ANONYMOUS_USER

GUARDIAN_GET_INIT_ANONYMOUS_USER
--------------------------------

.. versionadded:: 1.2

Guardian supports object level permissions for anonymous users, however when
in our project we use custom User model, default function might fail. This can
lead to issues as ``guardian`` tries to create anonymous user after each
``syncdb`` call. Object that is going to be created is retrieved using function
pointed by this setting. Once retrieved, ``save`` method would be called on
that instance.

Defaults to ``"guardian.management.get_init_anonymous_user"``.


.. seealso:: :ref:`custom-user-model-anonymous`
