from django import forms
from django.utils.translation import ugettext as _

from guardian.shortcuts import assign
from guardian.shortcuts import remove_perm
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_perms_for_model


class BaseObjectPermissionsForm(forms.Form):

    def __init__(self, obj, *args, **kwargs):
        self.obj = obj
        super(BaseObjectPermissionsForm, self).__init__(*args, **kwargs)
        field_name = self.get_obj_perms_field_name()
        self.fields[field_name] = self.get_obj_perms_field()

    def get_obj_perms_field(self):
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
        return 'permissions'

    def get_obj_perms_field_label(self):
        return _("Permissions")

    def get_obj_perms_field_choices(self):
        choices = [(p.codename, p.name) for p in get_perms_for_model(self.obj)]
        return choices

    def get_obj_perms_field_initial(self):
        return []

    def get_obj_perms_field_class(self):
        return forms.MultipleChoiceField

    def get_obj_perms_field_widget(self):
        return forms.SelectMultiple

    def are_obj_perms_required(self):
        return False

    def save_obj_perms(self):
        raise NotImplementedError


class UserObjectPermissionsForm(BaseObjectPermissionsForm):

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
            assign(perm, self.user, self.obj)


class GroupObjectPermissionsForm(BaseObjectPermissionsForm):

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
            assign(perm, self.group, self.obj)

