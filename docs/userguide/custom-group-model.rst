.. _custom-group-model:

Custom Group model
=================

.. versionadded:: 2.6

Django does not provide the same ability to create a custom ``auth.Group`` model
as the ``AbstractUser`` model and probably never will: https://code.djangoproject.com/ticket/29748.

In order to use guardian with a custom group model as it is done with a custom user model
(see :ref:`custom-user-model`), a custom :model:`GroupObjectPermission` model can be used.

Here is an example of using a custom group model with guardian:

.. code-block:: python

    from django.contrib.auth.models import PermissionsMixin

    class CustomGroupPermissionsMixin(PermissionsMixin):
        groups = models.ManyToManyField(
            "CustomGroup",
            verbose_name=_("groups"),
            blank=True,
            help_text=_(
                "The groups this user belongs to. A user will get all permissions "
                "granted to each of their groups."
            ),
            related_name="user_set",
            related_query_name="user",
        )

    class Meta(PermissionsMixin.Meta):
        abstract = True


This mixin will be used to override the ``groups`` field of the custom user model
with a field that uses the custom group model. It can be placed in ``myapp/mixins.py``.

Then, the custom user model and the custom group model can be defined as follows:

.. code-block:: python

    from .mixins import CustomGroupPermissionsMixin
    from guardian.mixins import GuardianUserMixin, GuardianGroupMixin

    class CustomGroup(Group, GuardianGroupMixin):
        foo = models.CharField(max_length=120)  # adds a custom field to the original Group model


    class User(AbstractBaseUser, CustomGroupPermissionsMixin, GuardianUserMixin):
        email = models.EmailField(
            verbose_name=_("email address"), max_length=200, unique=True, db_index=True
        )
        ...


    class CustomGroupObjectPermission(GroupObjectPermissionAbstract):
        group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)

        class Meta(GroupObjectPermissionAbstract.Meta):
            abstract = False


These models can be placed in ``myapp/models.py``. The ``CustomGroupObjectPermission`` will use
the custom group model instead of the default ``auth.Group`` model.

To access the ``CustomGroupObjectPermission`` model, the function ``get_group_obj_perms_model`` can be used:

.. code-block:: python

    from guardian.utils import get_group_obj_perms_model

    GroupObjectPermission = get_group_obj_perms_model()  # this returns the correct group permission model

    def return_all_group_obj_perms():
        return GroupObjectPermission.objects.all()


.. important::
    When using an custom :model:`GroupObjectPermission` model, do not import the :model:`GroupObjectPermission` model
    directly in your code, always use the ``get_group_obj_perms_model`` function
    (see :ref:`guardian-group-obj-perms-model`).

By default django-guardian monkey patches the group model to add some needed
functionality. This can result in errors if guardian is imported into the ``models.py``
of the same app where the custom group model lives.

To fix this, it is recommended to add the setting ``GUARDIAN_MONKEY_PATCH_GROUP = False``
in your ``settings.py`` and subclass ``guardian.mixins.GuardianGroupMixin`` in your custom group model.

The ``settings.py`` file for the example above would look like this:

.. code-block:: python

    ...
    GUARDIAN_MONKEY_PATCH_USER = False
    GUARDIAN_MONKEY_PATCH_GROUP = False
    GUARDIAN_GROUP_OBJ_PERMS_MODEL = 'myapp.CustomGroupObjectPermission'
    ...

