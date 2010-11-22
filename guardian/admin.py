from django import forms
from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from guardian.forms import UserObjectPermissionsForm
from guardian.forms import GroupObjectPermissionsForm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import get_groups_with_perms
from guardian.shortcuts import get_perms_for_model


class AdminUserObjectPermissionsForm(UserObjectPermissionsForm):

    def get_obj_perms_field_widget(self):
        return FilteredSelectMultiple(_("Permissions"), False)


class AdminGroupObjectPermissionsForm(GroupObjectPermissionsForm):

    def get_obj_perms_field_widget(self):
        return FilteredSelectMultiple(_("Permissions"), False)


class GuardedModelAdmin(admin.ModelAdmin):

    change_form_template = \
        'admin/guardian/model/change_form.html'
    obj_perms_manage_template = \
        'admin/guardian/model/obj_perms_manage.html'
    obj_perms_manage_user_template = \
        'admin/guardian/model/obj_perms_manage_user.html'
    obj_perms_manage_group_template = \
        'admin/guardian/model/obj_perms_manage_group.html'

    def get_urls(self):
        urls = super(GuardedModelAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        myurls = patterns('',
            url(r'^(?P<object_pk>.+)/permissions/$',
                view=self.admin_site.admin_view(self.obj_perms_manage),
                name='%s_%s_permissions' % info),
            url(r'^(?P<object_pk>.+)/permissions/user-manage/(?P<user_id>\d+)/$',
                view=self.admin_site.admin_view(self.obj_perms_manage_user),
                name='%s_%s_permissions_manage_user' % info),
            url(r'^(?P<object_pk>.+)/permissions/group-manage/(?P<group_id>\d+)/$',
                view=self.admin_site.admin_view(self.obj_perms_manage_group),
                name='%s_%s_permissions_manage_group' % info),
        ) + super(GuardedModelAdmin, self).get_urls()
        return myurls + urls

    def get_obj_perms_base_context(self, request, obj):
        context = {
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

    def obj_perms_manage(self, request, object_pk):
        obj = get_object_or_404(self.queryset(request), pk=object_pk)
        users_perms = SortedDict(
            get_users_with_perms(obj, attach_perms=True))
        users_perms.keyOrder.sort(key=lambda user: user.username)
        groups_perms = SortedDict(
            get_groups_with_perms(obj, attach_perms=True))
        groups_perms.keyOrder.sort(key=lambda group: group.name)

        if request.method == 'POST' and 'submit_manage_user' in request.POST:
            user_form = UserManage(request.POST)
            group_form = GroupManage()
            if user_form.is_valid():
                user_id = user_form.cleaned_data['user'].id
                url = request.META['PATH_INFO'] + 'user-manage/%d/' % user_id
                return redirect(url)
        elif request.method == 'POST' and 'submit_manage_group' in request.POST:
            user_form = UserManage()
            group_form = GroupManage(request.POST)
            if group_form.is_valid():
                group_id = group_form.cleaned_data['group'].id
                url = request.META['PATH_INFO'] + 'group-manage/%d/' % group_id
                return redirect(url)
        else:
            user_form = UserManage()
            group_form = GroupManage()

        context = self.get_obj_perms_base_context(request, obj)
        context['users_perms'] = users_perms
        context['groups_perms'] = groups_perms
        context['user_form'] = user_form
        context['group_form'] = group_form

        return render_to_response(self.obj_perms_manage_template,
            context, RequestContext(request))

    def get_obj_perms_manage_template(self):
        return self.obj_perms_manage_template

    def obj_perms_manage_user(self, request, object_pk, user_id):
        user = get_object_or_404(User, id=user_id)
        obj = get_object_or_404(self.queryset(request), pk=object_pk)
        form_class = self.get_obj_perms_manage_user_form()
        form = form_class(user, obj, request.POST or None)

        if request.method == 'POST' and form.is_valid():
            form.save_obj_perms()
            messages.success(request, "Permissions saved")
            return redirect(request.META['PATH_INFO'])

        context = self.get_obj_perms_base_context(request, obj)
        context['user_obj'] = user
        context['user_perms'] = get_perms(user, obj)
        context['form'] = form

        return render_to_response(self.get_obj_perms_manage_user_template(),
            context, RequestContext(request))

    def get_obj_perms_manage_user_template(self):
        return self.obj_perms_manage_user_template

    def get_obj_perms_manage_user_form(self):
        return AdminUserObjectPermissionsForm

    def obj_perms_manage_group(self, request, object_pk, group_id):
        group = get_object_or_404(Group, id=group_id)
        obj = get_object_or_404(self.queryset(request), pk=object_pk)
        form_class = self.get_obj_perms_manage_group_form()
        form = form_class(group, obj, request.POST or None)

        if request.method == 'POST' and form.is_valid():
            form.save_obj_perms()
            messages.success(request, _("Permissions saved"))
            return redirect(request.META['PATH_INFO'])

        context = self.get_obj_perms_base_context(request, obj)
        context['group_obj'] = group
        context['group_perms'] = get_perms(group, obj)
        context['form'] = form

        return render_to_response(self.get_obj_perms_manage_group_template(),
            context, RequestContext(request))

    def get_obj_perms_manage_group_template(self):
        return self.obj_perms_manage_group_template

    def get_obj_perms_manage_group_form(self):
        return AdminGroupObjectPermissionsForm


class UserManage(forms.Form):
    user = forms.RegexField(label=_("Username"), max_length=30,
        regex=r'^[\w.@+-]+$',
        error_messages = {
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters."),
            'does_not_exist': _("This user does not exist")})

    def clean_user(self):
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
        name = self.cleaned_data['group']
        try:
            group = Group.objects.get(name=name)
            return group
        except Group.DoesNotExist:
            raise forms.ValidationError(
                self.fields['group'].error_messages['does_not_exist'])



