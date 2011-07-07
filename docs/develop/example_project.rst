.. _example-project:

Example project
===============

Example project should be boundled with archive and be available at
``example_project``. Before you can run it, some requirements have to be met.
Those are easily installed using following command at example project's
directory::

    $ pip install -r requirements.txt

And last thing before we can run example project is to create sqlite database::

    $ python manage.py syncdb

Finally we can run dev server::

    $ python manage.py runserver

Project is really basic and shows almost nothing but eventually it should
expose some ``django-guardian`` functionality.

