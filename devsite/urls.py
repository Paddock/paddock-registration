from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from paddock.forms import UserCreationForm

urlpatterns = patterns('',
    # Examples:
    #url(r'clubs/','paddock.views.clubs')
    url(r'^paddock/',include('paddock.urls')),
    url(r'accounts/register/$','registration.views.register',
        {'form_class':UserCreationForm,
         'backend': 'registration.backends.default.DefaultBackend'},
        name='registration_register'),
    url(r'^accounts/', include('registration.backends.default.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
