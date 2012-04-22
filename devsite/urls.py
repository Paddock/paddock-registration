from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'clubs/','paddock.views.clubs')
    url(r'^paddock/',include('paddock.urls')),
    #url(r'^login/$','django.contrib.auth.views.login', 
    #    {'template_name':'paddock/login.html'}),
    #url(r'^logout/$','django.contrib.auth.views.logout',
    #    {'next_page':'/paddock/clubs'}),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
