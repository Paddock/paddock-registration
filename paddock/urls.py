from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    # Examples:
    url(r'^', include('registration.urls')),
    url(r'^password/', include('password_reset.urls')),
    url(r'^garage/', include('garage.urls')),
    #random numbers in url are for 'security'
    url(r'^paypal-ipn-handler/3995760248/', include('paypal.standard.ipn.urls')),
    #url(r'^profiler/', include('profiler.urls'))
)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
    )
