.. _admin-integration:

Admin integration
=================

Django comes with excellent and widely used *Admin* application. Basically,
it provides content management for Django applications. User with access to
admin panel can manage users, groups, permissions and other data provided by
system.

``django-guardian`` comes with simple object permissions management integration
for Django's admin application.

GuardedModelAdmin Approach
--------------------------

To proivde object level admin integration for your models use :admin:`GuardedModelAdmin`
instead of standard ``django.contrib.admin.ModelAdmin`` class for registering
models within the admin. In example, look at following model:

.. code-block:: python

    from django.db import models


    class Post(models.Model):
        title = models.CharField('title', max_length=64)
        slug = models.SlugField(max_length=64)
        content = models.TextField('content')
        created_at = models.DateTimeField(auto_now_add=True, db_index=True)

        class Meta:
            permissions = (
                ('view_post', 'Can view post'),
            )
            get_latest_by = 'created_at'

        def __unicode__(self):
            return self.title

        @models.permalink
        def get_absolute_url(self):
            return {'post_slug': self.slug}

We want to register ``Post`` model within admin application. Normally, we would
do this as follows within ``admin.py`` file of our application:

.. code-block:: python

    from django.contrib import admin

    from example_project.posts.models import Post


    class PostAdmin(admin.ModelAdmin):
        prepopulated_fields = {"slug": ("title",)}
        list_display = ('title', 'slug', 'created_at')
        search_fields = ('title', 'content')
        ordering = ('-created_at',)
        date_hierarchy = 'created_at'

    admin.site.register(Post, PostAdmin)


If we would like to add object permissions management for ``Post`` model we
would need to change ``PostAdmin`` base class into ``GuardedModelAdmin``.
Our code could look as follows:

.. code-block:: python

    from django.contrib import admin

    from example_project.posts.models import Post

    from guardian.admin import GuardedModelAdmin


    class PostAdmin(GuardedModelAdmin):
        prepopulated_fields = {"slug": ("title",)}
        list_display = ('title', 'slug', 'created_at')
        search_fields = ('title', 'content')
        ordering = ('-created_at',)
        date_hierarchy = 'created_at'

    admin.site.register(Post, PostAdmin)

And thats it. We can now navigate to **change** post page and just next to the
*history* link we can click *Object permissions* button to manage row level
permissions.

.. note::
   Example above is shipped with ``django-guardian`` package with the example
   project.

Django Existing Apps or Thrid Party Apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To provide admin object level permission support for third party app or existing Django app you must first unregister
the exsiting ModelAdmin and re-register one that is based on ``GuardedModelAdmin``. Using ``django.contrib.auth`` the 
user admin as an example we would first create a project level app called ``flatpages_ext`` and then create an ``admin.py``
file like so: 

.. code-block:: python

	from django.contrib.flatpages.admin import FlatPageAdmin
	from guardian.admin import GuardedModelAdmin
	
	class FlatPageExtAdmin(GuardedModelAdmin, FlatPageAdmin):
	    """ Our project tailored FlatPageAdmin """
	    pass
	
	admin.site.unregister(FlatPage)
	admin.site.register(FlatPage, FlatPageExtAdmin)

Monkeypatching Django Approach
------------------------------

This has the great benefit that existing Django models, third party apps, your models and future models - the entire 
Django site automatically gets object level permission support in the Admin. Monkeypatching might have negative perception
surrounding it however when done right it is a valuable programming tool - Python is a dynamic beast so embrace it:

.. code-block:: python

	import logging
	logger = logging.getLogger(__name__)
	# be nice and tell you are patching
	logger.info("Patching 'admin.ModelAdmin = GuardedModelAdmin': replace 'admin.ModelAdmin' with 'GuardedModelAdmin' "
				"which provides an ability to edit object level permissions.")
	# confirm signature of code we are patching and warn if it has changed
	if not '3c43401f585ae4a368c901e96f233981' == \
			hashlib.md5(inspect.getsource(admin.ModelAdmin)).hexdigest():
		logger.warn("md5 signature of 'admin.ModelAdmin' does not match Django 1.5. There is a slight change patch "
					"might be broken so please compare and update this monkeypatch.")
	admin.ModelAdmin = GuardedModelAdmin # apply the patch
	
There is no standard where to place this code, but you could create a project app ``settings`` or ``monkeypatches``, 
place the above code in file named ``patch_contrib_admin.py``, ensure it is auto imported in the apps ``__init__.py``.
and lastly include the app in the Django ``INSTALLED_APPS`` setting. 