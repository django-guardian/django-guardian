from itertools import chain

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, F

from permission_backend_nonrel.models import UserPermissionList
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.utils import get_identity

class ObjectPermissionChecker(object):
	"""
	Generic object permissions checker class being the heart of
	``django-guardian``.

	.. note::
	   Once checked for single object, permissions are stored and we don't hit
	   database again if another check is called for this object. This is great
	   for templates, views or other request based checks (assuming we don't
	   have hundreds of permissions on a single object as we fetch all
	   permissions for checked object).

	   On the other hand, if we call ``has_perm`` for perm1/object1, then we
	   change permission state and call ``has_perm`` again for same
	   perm1/object1 on same instance of ObjectPermissionChecker we won't see a
	   difference as permissions are already fetched and stored within cache
	   dictionary.
	"""
	def __init__(self, user_or_group=None):
		"""
		:param user_or_group: should be an ``User``, ``AnonymousUser`` or
		  ``Group`` instance
		"""
		self.user, self.group = get_identity(user_or_group)
		self._obj_perms_cache = {}

	def has_perm(self, perm, obj):
		"""
		Checks if user/group has given permission for object.

		:param perm: permission as string, may or may not contain app_label
		  prefix (if not prefixed, we grab app_label from ``obj``)
		:param obj: Django model instance for which permission should be checked

		"""
		perm = perm.split('.')[-1]
		if self.user and not self.user.is_active:
			return False
		elif self.user and self.user.is_superuser:
			return True
		return perm in self.get_perms(obj)

	def get_perms(self, obj):
		"""
		Returns list of ``codename``'s of all permissions for given ``obj``.

		:param obj: Django model instance for which permission should be checked

		"""
		ctype = ContentType.objects.get_for_model(obj)
		key = self.get_local_cache_key(obj)
		if not key in self._obj_perms_cache:
			if self.user and not self.user.is_active:
				return []
			elif self.user and self.user.is_superuser:
				perms = list(chain(*Permission.objects
					.filter(content_type=ctype)
					.values_list("codename")))
			elif self.user:
				user_perms = list(UserObjectPermission.objects\
					.filter(user=self.user)\
					.filter(content_type=ctype)\
					.filter(object_pk=obj.pk)\
					.values_list('permission', flat=True))
				group_pk_list = UserPermissionList.objects.get(user=self.user).group_fk_list
				group_perms = list(GroupObjectPermission.objects\
					.filter(content_type=ctype)\
					.filter(object_pk=obj.pk)\
					.filter(group__in=group_pk_list)\
					.values_list('permission', flat=True))
				user_perms.extend(group_perms)
				perms = list(set(Permission.objects\
					.filter(pk__in=user_perms)\
					.values_list('codename', flat=True)))
			else:
				group_perms = list(GroupObjectPermission.objects\
					.filter(content_type=ctype)\
					.filter(object_pk=obj.pk)\
					.filter(group=self.group)\
					.values_list('permission', flat=True))
				perms = list(set(Permission.objects\
					.filter(pk__in=group_perms)\
					.values_list('codename', flat=True)))
			self._obj_perms_cache[key] = perms
		return self._obj_perms_cache[key]

	def get_local_cache_key(self, obj):
		"""
		Returns cache key for ``_obj_perms_cache`` dict.
		"""
		ctype = ContentType.objects.get_for_model(obj)
		return (ctype.id, obj.pk)

