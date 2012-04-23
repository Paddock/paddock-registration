from django import forms

from django.contrib.auth.forms import AuthenticationForm as AF
from registration.forms import RegistrationForm as UCF
from bootstrap.forms import BootstrapMixin, Fieldset

class UserCreationForm(BootstrapMixin, UCF):
    pass

class AuthenticationForm(BootstrapMixin, AF):
    pass
