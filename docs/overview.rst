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

Alternate projects
------------------

Django_ still *only* has the foundation for object permissions [1]_ and
``django-guardian`` makes use of new facilities and it is based on them.  There
are some other pluggable applications which do *NOT* require Django_ version 1.2+. 
For instance, `django-authority`_ or
`django-permissions`_ are great options available.

.. _django: http://www.djangoproject.com/
.. _django-authority: https://github.com/jazzband/django-authority
.. _django-permissions: https://github.com/lambdalisue/django-permission
.. _issue-tracker: http://github.com/lukaszb/django-guardian
.. _grappelli: https://github.com/sehmaschine/django-grappelli

.. [1] See https://docs.djangoproject.com/en/stable/topics/auth/customizing/#handling-object-permissions
   for more detail.

