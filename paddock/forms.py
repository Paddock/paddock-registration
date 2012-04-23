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
    

class AuthenticationForm(BootstrapMixin, AF):
    pass
