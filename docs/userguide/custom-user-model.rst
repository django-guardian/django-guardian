.. _custom-user-model:

Custom User model
=================

.. versionadded:: 1.1

Django comes with the ability to customize default ``auth.User`` model
- either by subclassing ``AbstractUser`` or defining very own class. This can be
very powerful, it must be done with caution, though. Basically, if we subclass
``AbstractUser`` or define many-to-many relation with ``auth.Group`` (and give
reverse relate name **groups**) we should be fine.

By default django-guardian monkey patches the user model to add some needed
functionality. This can result in errors if guardian is imported into the models.py
of the same app where the custom user model lives.

To fix this, it is recommended to add the setting ``GUARDIAN_MONKEY_PATCH = False``
in your settings.py and subclass ``guardian.mixins.GuardianUserMixin`` in your custom user model.

.. important::
    ``django-guardian`` relies **heavily** on the ``auth.User`` model.
    Specifically it was build from the ground-up with relation between
    ``auth.User`` and ``auth.Group`` models. Retaining this relation is crucial
    for ``guardian`` - **without many to many User (custom or default) and
    auth.Group relation django-guardian will BREAK**.


.. seealso:: Read more about customizing User model
   here: https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model.


.. _custom-user-model-anonymous:

Anonymous user creation
-----------------------

It is also possible to override default behavior of how instance for anonymous
user is created. In example, let's imagine we have our user model as follows::


    from django.contrib.auth.models import AbstractUser
    from django.db import models


    class CustomUser(AbstractUser):
        real_username = models.CharField(max_length=120, unique=True)
        birth_date = models.DateField()  # field without default value

        USERNAME_FIELD = 'real_username'


Note that there is a ``birth_date`` field defined at the model and it does not
have a default value. It would fail to create anonymous user instance as
default implementation cannot know anything about ``CustomUser`` model.

In order to override the way anonymous instance is created we need to make
:setting:`GUARDIAN_GET_INIT_ANONYMOUS_USER` pointing at our custom
implementation. In example, let's define our init function::

    import datetime


    def get_anonymous_user_instance(User):
        return User(real_username='Anonymous', birth_date=datetime.date(1970, 1, 1))


and put it at ``myapp/models.py``. Last step is to set proper configuration in
our settings module::

    GUARDIAN_GET_INIT_ANONYMOUS_USER = 'myapp.models.get_anonymous_user_instance'
