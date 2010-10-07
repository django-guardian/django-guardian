from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from guardian.models import UserObjectPermission, GroupObjectPermission

class GroupObjectPermissionInline(GenericTabularInline):
    model = GroupObjectPermission
    ct_fk_field = 'object_pk'
    raw_id_fields = ['group']

class UserObjectPermissionInline(GenericTabularInline):
    model = UserObjectPermission
    ct_fk_field = 'object_pk'
    raw_id_fields = ['user']

class UserObjectPermissionAdmin(admin.ModelAdmin):
    list_display = ('permission', 'user', 'get_content')
    search_fields = (
        'permission__name',
        'permission__codename',
        'permission__content_type__app_label',
        'permission__content_type__model',
        'permission__content_type__name',
        'user__username',
        'user__first_name',
        'user__last_name',
    )

    def get_content(self, obj):
        change_url = reverse('admin:{0}_{1}_change'.format(obj.content_type.app_label, obj.content_type.model), args=[obj.object_pk])
        return mark_safe('<a href="{0}">{1}</a>'.format(change_url, obj.content_object))
    get_content.short_description = 'Content Object'
    get_content.allow_tags = True

admin.site.register(UserObjectPermission, UserObjectPermissionAdmin)

class GroupObjectPermissionAdmin(admin.ModelAdmin):
    list_display = ('permission', 'group', 'get_content')
    search_fields = (
        'permission__name',
        'permission__codename',
        'permission__content_type__app_label',
        'permission__content_type__model',
        'permission__content_type__name',
        'group__name'
    )

    def get_content(self, obj):
        change_url = reverse('admin:{0}_{1}_change'.format(obj.content_type.app_label, obj.content_type.model), args=[obj.object_pk])
        return mark_safe('<a href="{0}">{1}</a>'.format(change_url, obj.content_object))
    get_content.short_description = 'Content Object'
    get_content.allow_tags = True

admin.site.register(GroupObjectPermission, GroupObjectPermissionAdmin)
