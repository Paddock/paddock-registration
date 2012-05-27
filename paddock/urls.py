from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from forms import AuthenticationForm

urlpatterns = patterns('paddock.views',
    #url(r'^$','clubs'),
    url(r'^clubs/$','clubs'),
    url(r'^clubs/(?P<club_name>.*)/events/(?P<event_name>.*)$','event'),
    url(r'register/$','register'),
    url(r'activate/','activate'),
    url(r'^login/','login', 
        {'template_name':'paddock/login.html',
         'authentication_form':AuthenticationForm}),
    url(r'^logout/$','logout',
        {'next_page':'/paddock/clubs'}),    
    
)
