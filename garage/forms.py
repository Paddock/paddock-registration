from django.contrib.auth.forms import PasswordChangeForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class CrispyPasswordChangeForm(PasswordChangeForm): 

    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        self.helper.form_class = 'form-horizontal well'
        self.helper.form_method = 'post'
        self.helper.form_action = "#"

        self.helper.add_input(Submit('submit', 'Submit'))

        super(CrispyPasswordChangeForm, self).__init__(*args, **kwargs)