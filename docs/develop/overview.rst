.. _dev_overview:

Overview
========

Here we describe the development process overview. It's in F.A.Q. format to
make it simple.


Why devel is default branch?
----------------------------

Since version 1.2 we try to make ``master`` in a production-ready state. It
does NOT mean it is production ready, but it SHOULD be. In example, tests at
``master`` should always pass. Actually, whole tox suite should pass. And it's
test coverage should be at 100% level.

``devel`` branch, on the other hand, can break. It shouldn't but it is
acceptable. As a user, you should NEVER use non-master branches at production.
All the changes are pushed from ``devel`` to ``master`` before next release. It
might happen more frequently.


How to file a ticket?
---------------------

Just go to https://github.com/django-guardian/django-guardian/issues and create new
one.


How do I get involved?
----------------------

It's simple! If you want to fix a bug, extend documentation or whatever you
think is appropriate for the project and involves changes, just fork the
project at github (https://github.com/django-guardian/django-guardian), create a
separate branch, hack on it, publish changes at your fork and create a pull
request.

Here is a quick how to:

1. Fork a project: https://github.com/django-guardian/django-guardian/fork
2. Checkout project to your local machine::

       $ git clone git@github.com:YOUR_NAME/django-guardian.git

3. Create a new branch with name describing change you are going to work on::

       $ git checkout -b bugfix/support-for-custom-model

4. Perform changes at newly created branch. Remember to include tests (if this
   is code related change) and run test suite. See :ref:`running tests documentation
   <testing>`. Also, remember to add yourself to the ``AUTHORS`` file.
5. (Optional) Squash commits. If you have multiple commits and it doesn't make
   much sense to have them separated (and it usually makes little sense),
   please consider merging all changes into single commit. Please see
   https://help.github.com/articles/interactive-rebase if you need help with
   that.
6. Publish changes::

        $ git push origin YOUR_BRANCH_NAME

6. Create a Pull Request (https://help.github.com/articles/creating-a-pull-request).
   Usually it's as simple as opening up https://github.com/YOUR_NAME/django-guardian
   and clicking on review button for newly created branch. There you can make
   final review of your changes and if everything seems fine, create a Pull
   Request.


Why my issue/pull request was closed?
-------------------------------------

We usually put an explonation while we close issue or PR. It might be for
various reasons, i.e. there were no reply for over a month after our last
comment, there were no tests for the changes etc.


How to do a new release?
----------------------------

To enroll a new release you should perform the following task:

* Ensure file ``CHANGES`` reflects all important changes.
* Ensure file ``CHANGES`` includes a new version identifier and current release date.
* Execute ``bumpversion patch`` (or accordinly - see `Semantic Versioning 2.0 <http://semver.org/>`_ ) to reflects changes in codebase.
* Commit changes of codebase, e.g. ``git commit -m "Release 1.4.8" -a``.
* Tag a new release, e.g. ``git tag "v1.4.8"``.
* Push new tag to repo - ``git push origin --tags``.
* Build a new release - ``python3 setup.py sdist bdist_wheel``
* Push a new release to PyPI - ``twine upload``.
