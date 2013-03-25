from django.core.urlresolvers import reverse


from django.contrib.auth.forms import PasswordResetForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class ResetForm(PasswordResetForm): 

    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        self.helper.form_class = 'form-horizontal well'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('django.contrib.auth.views.password_reset')

        self.helper.add_input(Submit('submit', 'Submit'))

        super(ResetForm,self).__init__(*args, **kwargs)