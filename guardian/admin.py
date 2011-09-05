from django import forms
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext, ugettext_lazy as _

from guardian.forms import UserObjectPermissionsForm
from guardian.forms import GroupObjectPermissionsForm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import get_groups_with_perms
from guardian.shortcuts import get_perms_for_model


class AdminUserObjectPermissionsForm(UserObjectPermissionsForm):
    """
    Extends :form:`UserObjectPermissionsForm`. It only overrides
    ``get_obj_perms_field_widget`` method so it return
    ``django.contrib.admin.widgets.FilteredSelectMultiple`` widget.
    """
    def get_obj_perms_field_widget(self):
        return FilteredSelectMultiple(_("Permissions"), False)


class AdminGroupObjectPermissionsForm(GroupObjectPermissionsForm):
    """
    Extends :form:`GroupObjectPermissionsForm`. It only overrides
    ``get_obj_perms_field_widget`` method so it return
    ``django.contrib.admin.widgets.FilteredSelectMultiple`` widget.
    """
    def get_obj_perms_field_widget(self):
        return FilteredSelectMultiple(_("Permissions"), False)


class GuardedModelAdmin(admin.ModelAdmin):
    """
    Extends ``django.contrib.admin.ModelAdmin`` class. Provides some extra
    views for object permissions management at admin panel. It also changes
    default ``change_form_template`` option to
    ``'admin/guardian/model/change_form.html'`` which is required for proper
    url (object permissions related) being shown at the model pages.

    **Extra options**

    ``GuardedModelAdmin.obj_perms_manage_template``

        *Default*: ``admin/guardian/model/obj_perms_manage.html``

    ``GuardedModelAdmin.obj_perms_manage_user_template``

        *Default*: ``admin/guardian/model/obj_perms_manage_user.html``

    ``GuardedModelAdmin.obj_perms_manage_group_template``

        *Default*: ``admin/guardian/model/obj_perms_manage_group.html``

    ``GuardedModelAdmin.user_can_access_owned_objects_only``

        *Default*: ``False``

        If this would be set to ``True``, ``request.user`` would be used to
        filter out objects he or she doesn't own (checking ``user`` field
        of used model - field name may be overridden by
        ``user_owned_objects_field`` option.

        .. note::
           Please remember that this will **NOT** affect superusers!
           Admins would still see all items.

    ``GuardedModelAdmin.user_owned_objects_field``

        *Default*: ``user``

    **Usage example**

    Just use :admin:`GuardedModelAdmin` instead of
    ``django.contrib.admin.ModelAdmin``.

    .. code-block:: python

        from django.contrib import admin
        from guardian.admin import GuardedModelAdmin
        from myapp.models import Author

        class AuthorAdmin(GuardedModelAdmin):
            pass

        admin.site.register(Author, AuthorAdmin)

    """

    change_form_template = \
        'admin/guardian/model/change_form.html'
    obj_perms_manage_template = \
        'admin/guardian/model/obj_perms_manage.html'
    obj_perms_manage_user_template = \
        'admin/guardian/model/obj_perms_manage_user.html'
    obj_perms_manage_group_template = \
        'admin/guardian/model/obj_perms_manage_group.html'
    user_can_access_owned_objects_only = False
    user_owned_objects_field = 'user'

    def queryset(self, request):
        qs = super(GuardedModelAdmin, self).queryset(request)
        if self.user_can_access_owned_objects_only and \
            not request.user.is_superuser:
            filters = {self.user_owned_objects_field: request.user}
            qs = qs.filter(**filters)
        return qs

    def get_urls(self):
        """
        Extends standard admin model urls with the following:

        - ``.../permissions/``
        - ``.../permissions/user-manage/<user_id>/``
        - ``.../permissions/group-manage/<group_id>/``

        .. note::
           ``...`` above are standard, instance detail url (i.e.
           ``/admin/flatpages/1/``)

        """
        urls = super(GuardedModelAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        myurls = patterns('',
            url(r'^(?P<object_pk>.+)/permissions/$',
                view=self.admin_site.admin_view(self.obj_perms_manage_view),
                name='%s_%s_permissions' % info),
            url(r'^(?P<object_pk>.+)/permissions/user-manage/(?P<user_id>\-?\d+)/$',
                view=self.admin_site.admin_view(
                    self.obj_perms_manage_user_view),
                name='%s_%s_permissions_manage_user' % info),
            url(r'^(?P<object_pk>.+)/permissions/group-manage/(?P<group_id>\-?\d+)/$',
                view=self.admin_site.admin_view(
                    self.obj_perms_manage_group_view),
                name='%s_%s_permissions_manage_group' % info),
        )
        return myurls + urls

    def get_obj_perms_base_context(self, request, obj):
        """
        Returns context dictionary with common admin and object permissions
        related content.
        """
        context = {
            'adminform': {'model_admin': self},
            'object': obj,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'original': hasattr(obj, '__unicode__') and obj.__unicode__() or\
                str(obj),
            'has_change_permission': self.has_change_permission(request, obj),
            'model_perms': get_perms_for_model(obj),
            'title': _("Object permissions"),
        }
        return context

    def obj_perms_manage_view(self, request, object_pk):
        """
        Main object permissions view. Presents all users and groups with any
        object permissions for the current model *instance*. Users or groups
        without object permissions for related *instance* would **not** be
        shown. In order to add or manage user or group one should use links or
        forms presented within the page.
        """
        obj = get_object_or_404(self.queryset(request), pk=object_pk)
        users_perms = SortedDict(
            get_users_with_perms(obj, attach_perms=True,
                with_group_users=False))
        users_perms.keyOrder.sort(key=lambda user: user.username)
        groups_perms = SortedDict(
            get_groups_with_perms(obj, attach_perms=True))
        groups_perms.keyOrder.sort(key=lambda group: group.name)

        if request.method == 'POST' and 'submit_manage_user' in request.POST:
            user_form = UserManage(request.POST)
            group_form = GroupManage()
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.module_name
            )
            if user_form.is_valid():
                user_id = user_form.cleaned_data['user'].id
                url = reverse(
                    '%s:%s_%s_permissions_manage_user' % info,
                    args=[obj.pk, user_id]
                )
                return redirect(url)
        elif request.method == 'POST' and 'submit_manage_group' in request.POST:
            user_form = UserManage()
            group_form = GroupManage(request.POST)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.module_name
            )
            if group_form.is_valid():
                group_id = group_form.cleaned_data['group'].id
                url = reverse(
                    '%s:%s_%s_permissions_manage_group' % info,
                    args=[obj.pk, group_id]
                )
                return redirect(url)
        else:
            user_form = UserManage()
            group_form = GroupManage()

        context = self.get_obj_perms_base_context(request, obj)
        context['users_perms'] = users_perms
        context['groups_perms'] = groups_perms
        context['user_form'] = user_form
        context['group_form'] = group_form

        return render_to_response(self.get_obj_perms_manage_template(),
            context, RequestContext(request, current_app=self.admin_site.name))

    def get_obj_perms_manage_template(self):
        """
        Returns main object permissions admin template.  May be overridden if
        need to change it dynamically.

        .. note::
           If ``INSTALLED_APPS`` contains ``grappelli`` this function would
           return ``"admin/guardian/grappelli/obj_perms_manage.html"``.

        """
        if 'grappelli' in settings.INSTALLED_APPS:
            return 'admin/guardian/contrib/grappelli/obj_perms_manage.html'
        return self.obj_perms_manage_template

    def obj_perms_manage_user_view(self, request, object_pk, user_id):
        """
        Manages selected users' permissions for current object.
        """
        user = get_object_or_404(User, id=user_id)
        obj = get_object_or_404(self.queryset(request), pk=object_pk)
        form_class = self.get_obj_perms_manage_user_form()
        form = form_class(user, obj, request.POST or None)

        if request.method == 'POST' and form.is_valid():
            form.save_obj_perms()
            msg = ugettext("Permissions saved.")
            messages.success(request, msg)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.module_name
            )
            url = reverse(
                '%s:%s_%s_permissions_manage_user' % info,
                args=[obj.pk, user.id]
            )
            return redirect(url)

        context = self.get_obj_perms_base_context(request, obj)
        context['user_obj'] = user
        context['user_perms'] = get_perms(user, obj)
        context['form'] = form

        return render_to_response(self.get_obj_perms_manage_user_template(),
            context, RequestContext(request, current_app=self.admin_site.name))

    def get_obj_perms_manage_user_template(self):
        """
        Returns object permissions for user admin template.  May be overridden
        if need to change it dynamically.

        .. note::
           If ``INSTALLED_APPS`` contains ``grappelli`` this function would
           return ``"admin/guardian/grappelli/obj_perms_manage_user.html"``.

        """
        if 'grappelli' in settings.INSTALLED_APPS:
            return 'admin/guardian/contrib/grappelli/obj_perms_manage_user.html'
        return self.obj_perms_manage_user_template

    def get_obj_perms_manage_user_form(self):
        """
        Returns form class for user object permissions management.  By default
        :form:`AdminUserObjectPermissionsForm` is returned.
        """
        return AdminUserObjectPermissionsForm

    def obj_perms_manage_group_view(self, request, object_pk, group_id):
        """
        Manages selected groups' permissions for current object.
        """
        group = get_object_or_404(Group, id=group_id)
        obj = get_object_or_404(self.queryset(request), pk=object_pk)
        form_class = self.get_obj_perms_manage_group_form()
        form = form_class(group, obj, request.POST or None)

        if request.method == 'POST' and form.is_valid():
            form.save_obj_perms()
            msg = ugettext("Permissions saved.")
            messages.success(request, msg)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.module_name
            )
            url = reverse(
                '%s:%s_%s_permissions_manage_group' % info,
                args=[obj.pk, group.id]
            )
            return redirect(url)

        context = self.get_obj_perms_base_context(request, obj)
        context['group_obj'] = group
        context['group_perms'] = get_perms(group, obj)
        context['form'] = form

        return render_to_response(self.get_obj_perms_manage_group_template(),
            context, RequestContext(request, current_app=self.admin_site.name))

    def get_obj_perms_manage_group_template(self):
        """
        Returns object permissions for group admin template.  May be overridden
        if need to change it dynamically.

        .. note::
           If ``INSTALLED_APPS`` contains ``grappelli`` this function would
           return ``"admin/guardian/grappelli/obj_perms_manage_group.html"``.

        """
        if 'grappelli' in settings.INSTALLED_APPS:
            return 'admin/guardian/contrib/grappelli/obj_perms_manage_group.html'
        return self.obj_perms_manage_group_template

    def get_obj_perms_manage_group_form(self):
        """
        Returns form class for group object permissions management.  By default
        :form:`AdminGroupObjectPermissionsForm` is returned.
        """
        return AdminGroupObjectPermissionsForm


class UserManage(forms.Form):
    user = forms.RegexField(label=_("Username"), max_length=30,
        regex=r'^[\w.@+-]+$',
        error_messages = {
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."),
            'does_not_exist': _("This user does not exist")})

    def clean_user(self):
        """
        Returns ``User`` instance based on the given username.
        """
        username = self.cleaned_data['user']
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            raise forms.ValidationError(
                self.fields['user'].error_messages['does_not_exist'])


class GroupManage(forms.Form):
    group = forms.CharField(max_length=80, error_messages={'does_not_exist':
        _("This group does not exist")})

    def clean_group(self):
        """
        Returns ``Group`` instance based on the given group name.
        """
        name = self.cleaned_data['group']
        try:
            group = Group.objects.get(name=name)
            return group
        except Group.DoesNotExist:
            raise forms.ValidationError(
                self.fields['group'].error_messages['does_not_exist'])

