"""
``django-guardian`` template tags. To use in a template just put the following
*load* tag inside a template::

    {% load guardian_tags %}

"""
from django import template
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from guardian.core import ObjectPermissionChecker
from guardian.exceptions import NotUserNorGroup
from guardian.shortcuts import get_groups_with_perms

register = template.Library()

class ObjectPermissionsNode(template.Node):
    def __init__(self, for_whom, obj, context_var):
        self.for_whom = template.Variable(for_whom)
        self.obj = template.Variable(obj)
        self.context_var = context_var

    def render(self, context):
        for_whom = self.for_whom.resolve(context)
        if isinstance(for_whom, User):
            self.user = for_whom
            self.group = None
        elif isinstance(for_whom, AnonymousUser):
            self.user = User.get_anonymous()
            self.group = None
        elif isinstance(for_whom, Group):
            self.user = None
            self.group = for_whom
        else:
            raise NotUserNorGroup("User or Group instance required (got %s)"
                % for_whom.__class__)
        obj = self.obj.resolve(context)

        check = ObjectPermissionChecker(for_whom)
        perms = check.get_perms(obj)

        context[self.context_var] = perms
        return ''

@register.tag
def get_obj_perms(parser, token):
    """
    Returns a list of permissions (as ``codename`` strings) for a given
    ``user``/``group`` and ``obj`` (Model instance).

    Parses ``get_obj_perms`` tag which should be in format::

        {% get_obj_perms user/group for obj as "context_var" %}

    Example of usage (assuming ``flatpage`` and ``perm`` objects are
    available from *context*)::

        {% get_obj_perms request.user for flatpage as "flatpage_perms" %}

        {% if "delete_flatpage" in flatpage_perms %}
            <a href="/pages/delete?target={{ flatpage.url }}">Remove page</a>
        {% endif %}

    .. note::
       Please remember that superusers would always get full list of permissions
       for a given object.

    """
    bits = token.split_contents()
    format = '{% get_obj_perms user/group for obj as "context_var" %}'
    if len(bits) != 6 or bits[2] != 'for' or bits[4] != 'as':
        raise template.TemplateSyntaxError("get_obj_perms tag should be in "
            "format: %s" % format)

    for_whom = bits[1]
    obj = bits[3]
    context_var = bits[5]
    if context_var[0] != context_var[-1] or context_var[0] not in ('"', "'"):
        raise template.TemplateSyntaxError("get_obj_perms tag's context_var "
            "argument should be in quotes")
    context_var = context_var[1:-1]
    return ObjectPermissionsNode(for_whom, obj, context_var)


class ObjectGroupsNode(template.Node):
    """
    Returns a list of groups (as ``auth:model.Group`` instances) for a given
     ``obj`` (instance level permissions) or a ``model_class`` (Model level permissions)

    .. note:: for an object instance both Groups on the model level and instance level are 
              returned. Model level groups and instance level groups can be accessed
              through ``model_groups`` and ``instance_groups`` respectively. 

    Supported syntax tag syntax:

         {% get_obj_groups <obj> as \"<context_variable_name>\" %}
         {% get_obj_groups "<app_name:model_class>" as \"<context_variable_name>\" %}

    Example of usage (assuming ``flatpage`` is available from *context*)::

        {% get_obj_groups flatpage as "flatpage_group_list" %}
        
        <h1>{{flatpage}} access list</h1>
        {% for group in flatpage_group_list %}
            <h2>{{group.name}}</h2>
            <ul>
            {% for perm in group.permissions %}
            <li>{{perm}}</li>
            {% endfor %}
            </ul>
        {% endfor %}
        ...
        {{ flatpage_group_list.instance_groups }}
        {{ flatpage_group_list.model_groups }}
        ...
        {% for group in foo_group_list %}
            {% for perm in group.permissions.all %}
                {{perm.codename}}
            {% endfor %}
        {% endfor %}
    """
    def __init__(self, obj_or_model, as_variable_name):
        self.obj_or_model = obj_or_model # resolved in render method as needed
        self.as_variable_name = as_variable_name

    def render(self, context):
        ### check against an instance or a model class 
        if (self.obj_or_model[0] in ('"', "'")): # model class name and we also no it has passed all syntax checks
            app_model_name = self.obj_or_model.replace('"', '').replace("'", '').split(':')
            content_type = ContentType.objects.get(app_label=app_model_name[0], model=app_model_name[1])
            result_groups = Group.objects.filter(permissions__content_type=content_type).distinct()
            result_groups.instance_groups = None
            result_groups.model_groups = result_groups
        else: # we are getting groups for an instance
            instance = template.Variable(self.obj_or_model).resolve(context)
            instance_groups = get_groups_with_perms(instance)
            model_groups = Group.objects.filter(permissions__content_type=ContentType.objects.get_for_model(instance)).distinct()

            result_groups = instance_groups | model_groups
            result_groups.instance_groups = instance_groups
            result_groups.model_groups = model_groups

        context[self.as_variable_name] = result_groups
        return ''

@register.tag # this is just synonym with register.tag('get_obj_groups', get_obj_groups)
def get_obj_groups(parser, args):
    tag_template_syntax = "Tag's syntax is {%% %s <obj_instance OR \"app_name:model_class\"> as \"<context_variable_name>\" %%}"
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, obj_or_model, as_token, as_variable_name = args.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(tag_template_syntax % args.contents.split()[0])
    if not (as_variable_name[0] == as_variable_name[-1] and as_variable_name[0] in ('"', "'")):
        raise template.TemplateSyntaxError("Argument is not in quotes. " + tag_template_syntax % tag_name)
    if obj_or_model[0] in ('"', "'") and \
        (obj_or_model[0] != obj_or_model[-1] or not ':' in obj_or_model):
         raise template.TemplateSyntaxError("Missing \"app_name\" part. " + tag_template_syntax % tag_name)
    as_variable_name = as_variable_name.replace("\"", "").replace("\'", "")
    return ObjectGroupsNode(obj_or_model, as_variable_name)
