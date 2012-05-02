from django import forms

from django.contrib.auth.models import User

from django.contrib.auth.forms import UserCreationForm as UCF, AuthenticationForm as AF
from bootstrap.forms import BootstrapForm,BootstrapMixin, Fieldset

class UserCreationForm(BootstrapMixin, UCF):
    
    email = forms.EmailField(widget=forms.TextInput(),
                            max_length=75,
                            label=("E-mail"),
                            error_messages={'invalid':'please provide a valid email address'})    
    

class AuthenticationForm(BootstrapMixin, AF):
    pass

class ActivationForm(BootstrapForm): 
    
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
