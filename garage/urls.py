from django.conf.urls.defaults import patterns, include, url

from api import v1_api

urlpatterns = patterns('garage.views',
    url(r'^users/(?P<username>\w{3,})$', 'admin_user', name="admin_user"),
    url(r'^clubs/(?P<clubname>\w{3,})$', 'admin_club', name="admin_club"),
    url(r'^clubs/(?P<clubname>\w{3,})/membership/', 'new_membership'),
    url(r'^car_avatar/(?P<car_id>[0-9]+)$', 'car_avatar', name='car_avatar'),
    url(r'^event/(?P<event_id>[0-9]+)/email_drivers$', 'email_regd_drivers'),
    url(r'^event/(?P<event_id>[0-9]+)/reg_files$', 'reg_data_files'),
    url(r'^search_users/(?P<query>\w{3,})$', 'search_users'),
    url(r'api/', include(v1_api.urls)),
)
