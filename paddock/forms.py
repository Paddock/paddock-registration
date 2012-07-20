import urlparse
from functools import wraps
from django import forms
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect

from django.contrib.auth.models import User
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login

from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.decorators import available_attrs

from django.contrib.auth.forms import UserCreationForm as UCF, AuthenticationForm as AF

from django.forms import BooleanField
from bootstrap.forms import BootstrapModelForm,BootstrapForm,BootstrapMixin, Fieldset

from paddock.models import Registration, RaceClass

def form_is_for_self(form_class,form_field):
    """
    Decorator for views with forms that checks that the user is submitting a form to 
    edit themselves
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.method == 'POST': 
                form = form_class(request.POST)
                if form.data[form_field]== unicode(request.user.get_profile().pk): 
                    return view_func(request,*args,**kwargs)
                else: 
                    return HttpResponseRedirect(reverse('paddock.views.logout'))
            return view_func(request,*args,**kwargs)
        return _wrapped_view
    return decorator

class RegForm(BootstrapModelForm): 
    pax_class = forms.ModelChoiceField(queryset=RaceClass.objects.filter(pax_class=True).all(),
                label="Registration Series",
                empty_label = "Open Class", required=False)
    
    class Meta: 
        model = Registration
        #fields = ('number','race_class','pax_class')
        exclude = ['order','price','bump_class','checked_in','run_heat',
                   'work_heat','total_raw_time','total_index_time',
                   'class_points','index_points','_anon_f_name',
                   '_anon_l_name','_anon_car']  
        

class UserCreationForm(BootstrapMixin, UCF):
    
    email = forms.EmailField(widget=forms.TextInput(),
                            max_length=75,
                            label=("E-mail"),
                            error_messages={'invalid':'please provide a valid email address'})    
    

class AuthenticationForm(BootstrapMixin, AF):
    #monkey patch to adjust error messages
    error_messages = {
            'invalid_login': _("Please enter a correct username and password. "
                               "Note that both fields are case-sensitive."),
            'no_cookies': _("Your Web browser doesn't appear to have cookies "
                            "enabled. Cookies are required for logging in."),
            'inactive': _("This account is inactive. Please check your email for you activation code"),
        }  
    
    remember_me = BooleanField (
        label = _( 'Remember Me' ),
        initial = False,
        required = False,
        )

class ActivationForm(BootstrapForm): 
    class Meta: 
        layout = (
                    Fieldset("Enter the activation code sent to your email", "username", "activation_key", ),
                )        
        
    username = forms.RegexField(label="Username", max_length=30,
                                regex=r'^[\w.@+-]+$',
                                error_messages = {'invalid': "This value may contain only letters, numbers and "
                                                 "@/./+/-/_ characters."})
    
    activation_key = forms.fields.CharField(label="Activation key",max_length=40)
    
    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data.get("username")
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("This username is incorrect")   
        
        return username
    
    def clean(self):
        username = self.cleaned_data.get('username')
        activation_key = self.cleaned_data.get('activation_key')

        user = User.objects.get(username=username)
        p = user.get_profile()
        
        if p.activation_key != activation_key: 
            raise forms.ValidationError("This activation key is not valid")
        
        return self.cleaned_data
    
    

            