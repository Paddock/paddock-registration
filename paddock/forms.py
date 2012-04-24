from django import forms

from django.contrib.auth.models import User

from django.contrib.auth.forms import UserCreationForm as UCF, AuthenticationForm as AF
from bootstrap.forms import BootstrapMixin, Fieldset

class UserCreationForm(BootstrapMixin, UCF):
    class Meta:
        model = User
        layout = (
            Fieldset("Sign up", "username", "email", "password1","password2" ),
        )
    
    email = forms.EmailField(widget=forms.TextInput(),
                            max_length=75,
                            label=("E-mail"),
                            error_messages={'invalid':'please provide a valid email address'})    
    

class AuthenticationForm(BootstrapMixin, AF):
    pass
