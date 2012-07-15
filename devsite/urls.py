from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from paddock.forms import UserCreationForm
from django.conf import settings

urlpatterns = patterns('',
    # Examples:
    #url(r'clubs/','paddock.views.clubs')
    url(r'^paddock/',include('paddock.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
    )