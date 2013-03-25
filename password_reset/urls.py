from django.conf.urls.defaults import patterns, include, url

from forms import ResetForm

urlpatterns = patterns('',
    url(r'^reset/$', 
        'django.contrib.auth.views.password_reset', 
        {'post_reset_redirect': 'reset_done', 
         'template_name': 'password-reset/reset_form.html', 
         'password_reset_form': ResetForm},
        name="password_reset"),
    url(r'^reset/done/$',
        'django.contrib.auth.views.password_reset_done', 
        name="reset_done"),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        'django.contrib.auth.views.password_reset_confirm', 
        {'post_reset_redirect' : 'reset_complete'}),
    url(r'^user/password/done/$', 
        'django.contrib.auth.views.password_reset_complete', 
        name="reset_complete"),
)   