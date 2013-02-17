.. _custom-user-model:

Custom User model
=================

.. versionadded:: 1.1

Django 1.5 comes with the ability to customize default ``auth.User`` model
- either by subclassing ``AbstractUser`` or defining very own class. This can be
very powerful, it must be done with caution, though. Basically, if we subclass
``AbstractUser`` or define many-to-many relation with ``auth.Group`` (and give
reverse relate name **groups**) we should be fine.

.. important::
    ``django-guardian`` relies **heavily** on the ``auth.User`` model.
    Specifically it was build from the ground-up with relation beteen
    ``auth.User`` and ``auth.Group`` models. Retaining this relation is crucial
    for ``guardian`` - **without many to many User (custom or default) and
    auth.Group relation django-guardian will BREAK**.


.. seealso:: Read more about customizing User model introduced in Django 1.5
   here: https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#substituting-a-custom-user-model.
