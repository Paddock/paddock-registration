from django.conf.urls.defaults import patterns, include, url

from forms import ResetForm, SetForm

urlpatterns = patterns('',
    url(r'^reset/$', 
        'django.contrib.auth.views.password_reset', 
        {'template_name': 'password-reset/reset_form.html',
         'email_template_name':'password-reset/reset_email.txt',
         'subject_template_name':'password-reset/reset_subject.txt',
         'password_reset_form': ResetForm},
        name="password_reset"),
    url(r'^reset/done/$',
        'django.contrib.auth.views.password_reset_done', 
        {'template_name':'password-reset/reset_done.html'},
        name="reset_done"),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        'django.contrib.auth.views.password_reset_confirm', 
        {'template_name':'password-reset/reset_confirm.html', 
        'set_password_form': SetForm}),
    url(r'^user/password/done/$', 
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'password-reset/reset_complete.html'},
        name="reset_complete"),
)   