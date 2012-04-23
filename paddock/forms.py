from django import forms

from django.contrib.auth.forms import UserCreationForm as UCF, AuthenticationForm as AF
from bootstrap.forms import BootstrapMixin, Fieldset

class UserCreationForm(BootstrapMixin, UCF):
    
    email = forms.EmailField(label=("Email address"))

class AuthenticationForm(BootstrapMixin, AF):
    pass
