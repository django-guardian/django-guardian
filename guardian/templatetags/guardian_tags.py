"""
``django-guardian`` template tags. To use in a template just put the following
*load* tag inside a template::

    {% load guardian_tags %}

"""
from django import template
from django.template import get_library
from django.template import InvalidTemplateLibrary
from django.template.defaulttags import LoadNode

from guardian.exceptions import NotUserNorGroup
from guardian.core import ObjectPermissionChecker
from guardian.models import User, Group, AnonymousUser

register = template.Library()


@register.tag
def friendly_load(parser, token):
    '''
    Tries to load a custom template tag set. Non existing tag libraries
    are ignored.

    This means that, if used in conjuction with ``if_has_tag``, you can try to
    load the comments template tag library to enable comments even if the
    comments framework is not installed.

    For example::

        {% load friendly_loader %}
        {% friendly_load comments webdesign %}

        {% if_has_tag render_comment_list %}
            {% render_comment_list for obj %}
        {% else %}
            {% if_has_tag lorem %}
                {% lorem %}
            {% endif_has_tag %}
        {% endif_has_tag %}
    '''
    bits = token.contents.split()
    for taglib in bits[1:]:
        try:
            lib = get_library(taglib)
            parser.add_library(lib)
        except InvalidTemplateLibrary:
            pass
    return LoadNode()




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

    .. note::
       Make sure that you set and use those permissions in same template
       block (``{% block %}``).

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

