from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class ResetForm(PasswordResetForm): 

    def __init__(self, *args, **kwargs): 
        self.helper = FormHelper()

        self.helper.form_class = 'form-horizontal well'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('django.contrib.auth.views.password_reset')

        self.helper.add_input(Submit('submit', 'Submit'))

        super(ResetForm, self).__init__(*args, **kwargs)

class SetForm(SetPasswordForm): 

    def __init__(self, *args, **kwargs): 

        self.helper = FormHelper()

        self.helper.form_class = 'form-horizontal well'
        self.helper.form_method = 'POST'
        self.helper.form_action = "#"

        self.helper.add_input(Submit('submit', 'Submit'))
        
        super(SetForm, self).__init__(*args, **kwargs)    

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        #print "testing: ", self.cleaned_data['new_password1']
        super(SetForm,self).save(commit)  