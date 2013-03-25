from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    # Examples:
    url(r'^', include('registration.urls')),
    url(r'^password/', include('password_reset.urls')),
    url(r'^garage/', include('garage.urls'))

)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
    )
