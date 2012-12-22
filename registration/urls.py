from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.views.generic.simple import direct_to_template

from forms import AuthenticationForm
from api import v1_api

urlpatterns = patterns('registration.views',
    #url(r'^$','clubs'),
    url(r'^clubs/$', 'clubs'), 
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/$', 'event_register'),        
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/(?P<username>\w*)$', 'event_register'),    
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)$', 'event'),
    url(r'^users/(?P<username>\w{3,})/$', direct_to_template, {'template': 'registration/garage.html'}, name="garage"),
    url(r'^cars/(?P<car_id>[0-9]+)/$', 'car_avatar', name='car_avatar'),
    url(r'^register/$', 'register'),
    url(r'^activate/', 'activate'),
    url(r'^login/', 'login'),
    url(r'^logout/$', 'logout',
        {'next_page': '/paddock/clubs'}),
    url(r'api/', include(v1_api.urls)),
)