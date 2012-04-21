from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('paddock.views',
    #url(r'^$','clubs'),
    url(r'^clubs/$','clubs'),
    url(r'^users/new$','new_user'), #TODO: Check for proper rest convention
    url(r'^login/$','login', 
        {'template_name':'paddock/login.html'}),
    url(r'^logout/$','logout',
        {'next_page':'/paddock/clubs'}),    
    
)
