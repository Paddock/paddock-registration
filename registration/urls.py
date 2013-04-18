from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('registration.views',
    #url(r'^$','clubs'),
    url(r'^$', 'clubs'), 
    url(r'^clubs/(?P<club_name>\w+)$','club', name='club_detail'),
    url(r'^clubs/(?P<club_name>\w+)/renew_membership$', 'renew_membership', name='renew_membership'),
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/$', 'event_register'),        
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)/registration/(?P<username>\w*)$', 'event_register'),    
    url(r'^clubs/(?P<club_name>\w+)/seasons/(?P<season_year>[0-9]+)/events/(?P<event_name>\w+)$', 'event'),
    url(r'^register/$', 'register'),
    url(r'^activate/(?P<username>[\w\'\.\-]+)', 'activate'),
    url(r'^reactivate/(?P<username>[\w\'\.\-]+)', 'resend_activation_code'),
    url(r'^login/', 'login', name="login"),
    url(r'^logout/$', 'logout',
        {'next_page': '/'}),
)
