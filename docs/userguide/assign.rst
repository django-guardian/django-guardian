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
        reported_by = models.ForeignKey(User)
        created_at = models.DateTimeField(auto_now_add=True)

... and we want to be able to set custom permission *view_task*. We let know
Django to do so by adding ``permissions`` tuple to ``Meta`` class and our final
model could look like:

.. code-block:: python

    class Task(models.Model):
        summary = models.CharField(max_length=32)
        content = models.TextField()
        reported_by = models.ForeignKey(User)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            permissions = (
                ('view_task', 'View task'),
            )

After we call ``syncdb`` management command our *view_task* permission would be
added to default set of permissions.

.. note::
   By default, Django adds 3 permissions for each registered model:

   - *add_modelname*
   - *change_modelname*
   - *delete_modelname*

   (where *modelname* is a simplified name of our model's class). See
   http://docs.djangoproject.com/en/1.2/topics/auth/#default-permissions for
   more detail.

There is nothing new here since creation of permissions is 
`handled by django <http://docs.djangoproject.com/en/1.2/topics/auth/#id1>`_.
Now we can move to :ref:`assigning object permissions <assign-obj-perms>`.

.. _assign-obj-perms:

Assign object permissions
-------------------------

We can assign permissions for any user/group and object pairs using same,
convenient function: :func:`guardian.shortcuts.assign`.

For user
~~~~~~~~

Continuing our example we now can allow Joe user to view some task:

.. code-block:: python

    >>> boss = User.objects.create(username='Big Boss')
    >>> joe = User.objects.create(username='joe')
    >>> task = Task.objects.create(summary='Some job', content='', reported_by=boss)
    >>> joe.has_perm('view_task', task)
    False

Well, not so fast Joe, let us create an object permission finally:

.. code-block:: python

    >>> from guardian.shortcuts import assign
    >>> assign('view_task', joe, task)
    >>> joe.has_perm('view_task', task)
    True


For group
~~~~~~~~~

This case doesn't really differ from user permissions assignment. The only
difference is we have to pass ``Group`` instance rather than ``User``.

.. code-block:: python

    >>> group = Group.objects.create(name='employees')
    >>> assign('change_task', group, task)
    >>> joe.has_perm('change_task', task)
    False
    >>> # Well, joe is not yet within an *employees* group
    >>> joe.groups.add(group)
    >>> joe.has_perm('change_task', task)
    True
    
