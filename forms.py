
from django.contrib.auth.forms import UserCreationForm as UCF, AuthenticationForm as AF
from bootstrap.forms import BootstrapMixin, Fieldset

class UserCreationForm(BootstrapMixin, UCF):
    pass

class AuthenticationForm(BootstrapMixin, AF):
    pass
