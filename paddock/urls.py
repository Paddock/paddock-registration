from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from forms import AuthenticationForm
from api import v1_api



urlpatterns = patterns('paddock.views',
    #url(r'^$','clubs'),
    url(r'^clubs/$','clubs'), 
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/$','event_register'),        
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/(?P<username>\w*)$','event_register'),    
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)$','event'),
    url(r'^register/$','register'),
    url(r'^activate/','activate'),
    url(r'^login/','login', 
        {'template_name':'paddock/login.html',
         'authentication_form':AuthenticationForm}),
    url(r'^logout/$','logout',
        {'next_page':'/paddock/clubs'}),
    url(r'api/',include(v1_api.urls)),
)
