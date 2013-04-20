from functools import wraps
from django import forms
from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect

from django.contrib.auth.models import User
#from django.contrib.auth import REDIRECT_FIELD_NAME
#from django.contrib.auth.views import redirect_to_login

from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import available_attrs

from django.contrib.auth.forms import UserCreationForm as UCF, AuthenticationForm as AF

from django.forms import (BooleanField, Form, ModelForm, HiddenInput, 
    CharField)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from registration.models import Registration, RaceClass, Coupon


def form_is_for_self(form_class, form_field):
    """
    Decorator for views with forms that checks that the user is submitting a form to 
    edit themselves
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.method == 'POST':
                form = form_class(request.POST)
                if form.data[form_field] == unicode(request.user.get_profile().pk): 
                    return view_func(request, *args, **kwargs)
                else: 
                    return HttpResponseRedirect(reverse('registration.views.logout'))
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class CarAvatarForm(Form): 
    avatar = forms.ImageField()
    user_profile = forms.IntegerField()


class ClassChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, race_class):
            return race_class.abrv 


class CarChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, car):
            return "%s: %d %s %s"%(car.name, car.year, car.make, car.model)              


class RegForm(ModelForm): 
    pax_class = ClassChoiceField(queryset=RaceClass.objects.filter(pax_class=True).all(),
                                 label="Registration Series",
                                 empty_label="Open Class", required=False)
    race_class = ClassChoiceField(queryset=RaceClass.objects.
                                  filter(pax_class=False, bump_class=False).
                                  order_by('abrv').all(),
                                  label="Race Class")
    prepay = BooleanField(
        initial=False, required=False)
    
    coupon_code = CharField(required=False)

    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = "#"

        self.helper.add_input(Submit('submit', 'Submit'))

        #used for coupon code checking
        self.user = kwargs.get('user')
        if self.user: 
            del kwargs['user']
        super(RegForm,self).__init__(*args,**kwargs)

    def clean_coupon_code(self): 
        code = self.cleaned_data.get('coupon_code')
        self.coupon = None
        if code: 
            allowed = True
            try: 
                c = Coupon.objects.get(code=code)
                allowed = c.is_valid(self.user)
                self.coupon = c
            except: 
                allowed=False

            if not allowed: 
                    raise forms.ValidationError(u'Invalid Coupon Code')
        return code

    #TODO: Define some javascript to show/hide coupon code 
    #  and change button text to/from (Register/Checout with Paypal)

    #todo add verify function to check for valid coupon code...
    
    class Meta: 
        model = Registration
        #fields = ('number','race_class','pax_class')
        exclude = ('order', 'price', 'bump_class', 'checked_in', 'run_heat',
                   'work_heat', 'total_raw_time', 'total_index_time',
                   'class_points', 'index_points', '_anon_f_name',
                   '_anon_l_name', '_anon_car', 'paid')  
        

class UserCreationForm(UCF):

    first_name = forms.CharField()
    last_name = forms.CharField()
    
    email = forms.EmailField(widget=forms.TextInput(),
                             max_length=75,
                             label=("E-mail"),
                             error_messages={'invalid': 'please provide a valid email address'})    

    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('registration.views.register')

        self.helper.add_input(Submit('submit', 'Submit'))
        super(UserCreationForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError(u'This email address is already registered.')
        return email    
    


class AuthenticationForm(AF):
    #monkey patch to adjust error messages
    error_messages = {
        'invalid_login': _("Please enter a correct username and password. "
                           "Note that both fields are case-sensitive."),
        'no_cookies': _("Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in."),
        'inactive': _("This account is inactive. Please check your email for you activation code"),
    }  
    
    remember_me = BooleanField(
        label=_('Remember Me'),
        initial=False,
        required=False,
    )

    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        #self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'well form-horizontal'
        self.helper.form_method = 'post'
        #self.helper.form_action = reverse('registration.views.login')
        self.helper.form_tag = False

        self.helper.add_input(Submit('submit', 'Submit'))
        super(AuthenticationForm, self).__init__(*args, **kwargs)


class ActivationForm(Form): 
    #class Meta: 
        #layout = (
        #            Fieldset("Enter the activation code sent to your email", "username", "activation_key", ),
        #        )        
        
    username = forms.RegexField(label="Username", max_length=30,
                                regex=r'^[\w.@+-]+$',
                                error_messages={'invalid': "This value may contain only letters, numbers and "
                                "@/./+/-/_ characters."}, 
                                widget=HiddenInput())
    
    activation_key = forms.fields.CharField(label="Activation key", max_length=40)
    
    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        #self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'well form-horizontal'
        self.helper.form_method = 'post'
        #self.helper.form_action = reverse('registration.views.login')
        self.helper.form_tag = False

        self.helper.add_input(Submit('submit', 'Submit'))
        super(ActivationForm, self).__init__(*args, **kwargs)

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