.. _assign:

Assign object permissions
=========================

Assigning object permissions should be very simple once permissions are created
for models.

Prepare permissions
-------------------

Let's assume we have following model:

.. code-block:: python

    class Task(models.Model):
        summary = models.CharField(max_length=32)
        content = models.TextField()
        reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
        created_at = models.DateTimeField(auto_now_add=True)

... and we want to be able to set custom permission *assign_task*. We let Django
know to do so by adding ``permissions`` tuple to ``Meta`` class and our final
model could look like:

.. code-block:: python

    class Task(models.Model):
        summary = models.CharField(max_length=32)
        content = models.TextField()
        reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            permissions = (
                ('assign_task', 'Assign task'),
            )

After we call management commands ``makemigrations`` and ``migrate``
our *assign_task* permission would be added to default set of permissions.

.. note::
   By default, Django adds 4 permissions for each registered model:

   - *add_modelname*
   - *change_modelname*
   - *delete_modelname*
   - *view_modelname*

   (where *modelname* is a simplified name of our model's class). See
   https://docs.djangoproject.com/en/stable/topics/auth/default/#default-permissions for
   more detail.

There is nothing new here since creation of permissions is
`handled by django <https://docs.djangoproject.com/en/stable/topics/auth/>`_.
Now we can move to :ref:`assigning object permissions <assign-obj-perms>`.

.. _assign-obj-perms:

Assign object permissions
-------------------------

We can assign permissions for any user/group and object pairs using same,
convenient function: :func:`guardian.shortcuts.assign_perm`.

For user
~~~~~~~~

Continuing our example we now can allow Joe user to assign some task:

.. code-block:: python

    >>> from django.contrib.auth.models import User
    >>> boss = User.objects.create(username='Big Boss')
    >>> joe = User.objects.create(username='joe')
    >>> task = Task.objects.create(summary='Some job', content='', reported_by=boss)
    >>> joe.has_perm('assign_task', task)
    False

Well, not so fast Joe, let us create an object permission finally:

.. code-block:: python

    >>> from guardian.shortcuts import assign_perm
    >>> assign_perm('assign_task', joe, task)
    >>> joe.has_perm('assign_task', task)
    True


For group
~~~~~~~~~

This case doesn't really differ from user permissions assignment. The only
difference is we have to pass ``Group`` instance rather than ``User``.

.. code-block:: python

    >>> from django.contrib.auth.models import Group
    >>> group = Group.objects.create(name='employees')
    >>> assign_perm('change_task', group, task)
    >>> joe.has_perm('change_task', task)
    False
    >>> # Well, joe is not yet within an *employees* group
    >>> joe.groups.add(group)
    >>> joe.has_perm('change_task', task)
    True

Another example:

.. code-block:: python

    >>> from django.contrib.auth.models import User, Group
    >>> from guardian.shortcuts import assign_perm
    # fictional companies
    >>> company_a = Company.objects.create(name="Company A")
    >>> company_b = Company.objects.create(name="Company B")
    # create groups
    >>> company_user_group_a = Group.objects.create(name="Company User Group A")
    >>> company_user_group_b = Group.objects.create(name="Company User Group B")
    # assign object specific permissions to groups
    >>> assign_perm('change_company', company_user_group_a, company_a)
    >>> assign_perm('change_company', company_user_group_b, company_b)
    # create user and add it to one group for testing
    >>> user_a = User.objects.create(username="User A")
    >>> user_a.groups.add(company_user_group_a)
    >>> user_a.has_perm('change_company', company_a)
    True
    >>> user_a.has_perm('change_company', company_b)
    False
    >>> user_b = User.objects.create(username="User B")
    >>> user_b.groups.add(company_user_group_b)
    >>> user_b.has_perm('change_company', company_a)
    False
    >>> user_b.has_perm('change_company', company_b)
    True

Assigning Permissions inside Signals
------------------------------------
Note that the Anonymous User is created before the Permissions are created.
This may result in Django signals, e.g. ``post_save`` being sent before the
Permissions are created. You will need to take this into an account when
processing the signal.


..  code-block:: python

    @receiver(post_save, sender=User)
    def user_post_save(sender, **kwargs):
        """
        Create a Profile instance for all newly created User instances. We only
        run on user creation to avoid having to check for existence on each call
        to User.save.
        """
        user, created = kwargs["instance"], kwargs["created"]
        if created and user.username != settings.ANONYMOUS_USER_NAME:
            from profiles.models import Profile
            profile = Profile.objects.create(pk=user.pk, user=user, creator=user)
            assign_perm("change_user", user, user)
            assign_perm("change_profile", user, profile)

The check for ``user.username != settings.ANONYMOUS_USER_NAME`` is required otherwise
the ``assign_perm`` calls will occur when the Anonymous User is created,
however before there are any permissions available.
