from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import REDIRECT_FIELD_NAME
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.utils.html import urlquote
from django.utils.decorators import method_decorator


class LoginRequiredMixin(object):
    """ 
    A login required mixin for use with class based views. This Class is a light wrapper around the
    `login_required` decorator and hence function parameters are just attributes defined on the class.
    
    Due to parent class order traversal this mixin must be added as the left most 
    mixin of a view.
    
    The mixin has exaclty the same flow as `login_required` decorator:
    
        If the user isn't logged in, redirect to settings.LOGIN_URL, passing the current 
        absolute path in the query string. Example: /accounts/login/?next=/polls/3/.
        
        If the user is logged in, execute the view normally. The view code is free to 
        assume the user is logged in.

    **Class Settings**
        `redirect_field_name - defaults to "next"
        `login_url` - the login url of your site
        
    """
    redirect_field_name = REDIRECT_FIELD_NAME
    login_url = None
    
    @method_decorator(login_required(redirect_field_name=redirect_field_name, login_url=login_url))
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
    
class PermissionRequiredMixin(object):
    """ 
    A view mixin that verifies if the current logged in user has the specified permission 
    by wrapping the ``request.user.has_perm(..)`` method.
     
    If a `get_object()` method is defined either manually or by including another mixin (for example
    ``SingleObjectMixin``) or ``self.object`` is defiend then the permission will be tested against 
    that specific instance.
    
    .. NOTE: Testing of a permission against a specific object instance requires an authentication backend
             that supports. Please see ``django-guardian`` to add object level permissions to your project.  
    
    The mixin does the following:  
    
        If the user isn't logged in, redirect to settings.LOGIN_URL, passing the current 
        absolute path in the query string. Example: /accounts/login/?next=/polls/3/.
            
        If the `raise_exception` is set to True than rather than redirect to login page
        a `PermisionDenied` (403) is raised.
        
        If the user is logged in, and passes the permission check than the view is executed
        normally.

    **Example Usage**
        
        class FitterEditView(PermissionRequiredMixin, UpdateView):
            ...
            ### PermissionRequiredMixin settings
            permission_required = 'fitters.change_fitter'
            
            ### other view settings
            context_object_name="fitter"
            queryset = Fitter.objects.all()
            form_class = FitterForm
            ...

    **Class Settings**
        `permission_required` - the permission to check of form "<app_label>.<permission codename>"
                                i.e. 'polls.can_vote' for a permission on a model in the polls application.
                                
        `login_url` - the login url of your site
        `redirect_field_name - defaults to "next"
        `raise_exception` - defaults to False - raise PermisionDenied (403) if set to True
        
    """
    ### default class view settings
    login_url = settings.LOGIN_URL
    raise_exception = False
    permission_required = None
    redirect_field_name=REDIRECT_FIELD_NAME
    
    def dispatch(self, request, *args, **kwargs):
        # call the parent dispatch first to pre-populate few things before we check for permissions
        original_return_value = super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)
        
        # verify class settings
        if self.permission_required == None or len(self.permission_required.split('.')) != 2:
            raise ImproperlyConfigured("'PermissionRequiredMixin' requires 'permission_required' attribute to be set to '<app_label>.<permission codename>' but is set to '%s' instead" % self.permission_required)
        
        # verify permission on object instance if needed
        has_permission = False
        if hasattr(self, 'object')  and self.object is not None: 
            has_permission = request.user.has_perm(self.permission_required, self.object)
        elif hasattr(self, 'get_object') and callable(self.get_object):
            has_permission = request.user.has_perm(self.permission_required, self.get_object())
        else:
            has_permission = request.user.has_perm(self.permission_required)

        # user failed permission
        if not has_permission:
            if self.raise_exception:
                return HttpResponseForbidden()
            else:
                path = urlquote(request.get_full_path())
                tup = self.login_url, self.redirect_field_name, path
                return HttpResponseRedirect("%s?%s=%s" % tup)
                   
        # user passed permission check so just return the result of calling .dispatch()
        return original_return_value
