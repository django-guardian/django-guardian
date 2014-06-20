.. _overview:

Overview
========

``django-guardian`` is an implementation of object permissions for Django_
providing an extra *authentication backend*.

Features
--------

- Object permissions for Django_
- AnonymousUser support
- High level API
- Heavily tested
- Django's admin integration
- Decorators

Incoming
--------

- Admin templates for grappelli_

Source and issue tracker
------------------------

Sources are available at `issue-tracker`_. You may also file a bug there.

Alternatives
------------

Django_ 1.2 still has the *only* foundation for object permissions [1]_ and
``django-guardian`` makes use of new facilities and it is based on them.  There
are some other pluggable applications which do *NOT* require the latest 1.2
version of Django_. For instance, `django-authority`_ or
`django-permissions`_ are great and available for use with a <=1.2 Django project.

.. _django: http://www.djangoproject.com/
.. _django-authority: http://bitbucket.org/jezdez/django-authority/
.. _django-permissions: http://bitbucket.org/diefenbach/django-permissions/
.. _issue-tracker: http://github.com/lukaszb/django-guardian
.. _grappelli: https://github.com/sehmaschine/django-grappelli

.. [1] See http://docs.djangoproject.com/en/1.2/topics/auth/#handling-object-permissions
   for more detail.

