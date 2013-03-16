from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('registration.views',
    #url(r'^$','clubs'),
    url(r'^clubs/$', 'clubs'), 
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/$', 'event_register'),        
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/(?P<username>\w*)$', 'event_register'),    
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)$', 'event'),
    url(r'^register/$', 'register'),
    url(r'^activate/', 'activate'),
    url(r'^login/', 'login'),
    url(r'^logout/$', 'logout',
        {'next_page': '/clubs'}),
)
