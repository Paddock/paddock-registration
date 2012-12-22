from django.conf.urls.defaults import patterns, include, url

from api import v1_api

urlpatterns = patterns('garage.views',
    url(r'^users/(?P<user_id>[0-9]+)$', 'admin_user', name="admin_user"),
    url(r'^clubs/(?P<user_id>[0-9]+)$', 'admin_club', name="admin_club"),
    url(r'^cars/(?P<car_id>[0-9]+)/$', 'car_avatar', name='car_avatar'),
    url(r'api/', include(v1_api.urls)),
)