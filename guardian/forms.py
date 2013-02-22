from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext as _

from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_perms_for_model


class BaseObjectPermissionsForm(forms.Form):
    """
    Base form for object permissions management. Needs to be extended for usage
    with users and/or groups.
    """

    def __init__(self, obj, *args, **kwargs):
        """
        :param obj: Any instance which form would use to manage object
          permissions"
        """
        self.obj = obj
        super(BaseObjectPermissionsForm, self).__init__(*args, **kwargs)
        field_name = self.get_obj_perms_field_name()
        self.fields[field_name] = self.get_obj_perms_field()

    def get_obj_perms_field(self):
        """
        Returns field instance for object permissions management. May be
        replaced entirely.
        """
        field_class = self.get_obj_perms_field_class()
        field = field_class(
            label=self.get_obj_perms_field_label(),
            choices=self.get_obj_perms_field_choices(),
            initial=self.get_obj_perms_field_initial(),
            widget=self.get_obj_perms_field_widget(),
            required=self.are_obj_perms_required(),
        )
        return field

    def get_obj_perms_field_name(self):
        """
        Returns name of the object permissions management field. Default:
        ``permission``.
        """
        return 'permissions'

    def get_obj_perms_field_label(self):
        """
        Returns label of the object permissions management field. Defualt:
        ``_("Permissions")`` (marked to be translated).
        """
        return _("Permissions")

    def get_obj_perms_field_choices(self):
        """
        Returns choices for object permissions management field. Default:
        list of tuples ``(codename, name)`` for each ``Permission`` instance
        for the managed object.
        """
        choices = [(p.codename, p.name) for p in get_perms_for_model(self.obj)]
        return choices

    def get_obj_perms_field_initial(self):
        """
        Returns initial object permissions management field choices. Default:
        ``[]`` (empty list).
        """
        return []

    def get_obj_perms_field_class(self):
        """
        Returns object permissions management field's base class. Default:
        ``django.forms.MultipleChoiceField``.
        """
        return forms.MultipleChoiceField

    def get_obj_perms_field_widget(self):
        """
        Returns object permissions management field's widget base class.
        Default: ``django.forms.SelectMultiple``.
        """
        return forms.SelectMultiple

    def are_obj_perms_required(self):
        """
        Indicates if at least one object permission should be required. Default:
        ``False``.
        """
        return False

    def save_obj_perms(self):
        """
        Must be implemented in concrete form class. This method should store
        selected object permissions.
        """
        raise NotImplementedError


class UserObjectPermissionsForm(BaseObjectPermissionsForm):
    """
    Object level permissions management form for usage with ``User`` instances.

    Example usage::

        from django.shortcuts import get_object_or_404
        from myapp.models import Post
        from guardian.forms import UserObjectPermissionsForm
        from django.contrib.auth.models import User

        def my_view(request, post_slug, user_id):
            user = get_object_or_404(User, id=user_id)
            post = get_object_or_404(Post, slug=post_slug)
            form = UserObjectPermissionsForm(user, post, request.POST or None)
            if request.method == 'POST' and form.is_valid():
                form.save_obj_perms()
            ...

    """

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserObjectPermissionsForm, self).__init__(*args, **kwargs)

    def get_obj_perms_field_initial(self):
        perms = get_perms(self.user, self.obj)
        return perms

    def save_obj_perms(self):
        """
        Saves selected object permissions by creating new ones and removing
        those which were not selected but already exists.

        Should be called *after* form is validated.
        """
        perms = self.cleaned_data[self.get_obj_perms_field_name()]
        model_perms = [c[0] for c in self.get_obj_perms_field_choices()]

        to_remove = set(model_perms) - set(perms)
        for perm in to_remove:
            remove_perm(perm, self.user, self.obj)

        for perm in perms:
            assign_perm(perm, self.user, self.obj)


class GroupObjectPermissionsForm(BaseObjectPermissionsForm):
    """
    Object level permissions management form for usage with ``Group`` instances.

    Example usage::

        from django.shortcuts import get_object_or_404
        from myapp.models import Post
        from guardian.forms import GroupObjectPermissionsForm
        from guardian.models import Group

        def my_view(request, post_slug, group_id):
            group = get_object_or_404(Group, id=group_id)
            post = get_object_or_404(Post, slug=post_slug)
            form = GroupObjectPermissionsForm(group, post, request.POST or None)
            if request.method == 'POST' and form.is_valid():
                form.save_obj_perms()
            ...

    """

    def __init__(self, group, *args, **kwargs):
        self.group = group
        super(GroupObjectPermissionsForm, self).__init__(*args, **kwargs)

    def get_obj_perms_field_initial(self):
        perms = get_perms(self.group, self.obj)
        return perms

    def save_obj_perms(self):
        """
        Saves selected object permissions by creating new ones and removing
        those which were not selected but already exists.

        Should be called *after* form is validated.
        """
        perms = self.cleaned_data[self.get_obj_perms_field_name()]
        model_perms = [c[0] for c in self.get_obj_perms_field_choices()]

        to_remove = set(model_perms) - set(perms)
        for perm in to_remove:
            remove_perm(perm, self.group, self.obj)

        for perm in perms:
            assign_perm(perm, self.group, self.obj)

