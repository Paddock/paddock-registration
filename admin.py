from paddock.models import Club,Location
from django.contrib import admin

class LocationInline(admin.StackedInline):
    model = Location
    extra = 1
    
    fields = ['name','address']

class ClubAdmin(admin.ModelAdmin):
    fieldsets =[
        ('Club Information',{'fields':['club_name',
                                       'new_member_cost',
                                       'renew_cost',
                                       'membership_terms']}),
        ('Payment Processing',{'fields':['process_payments',
                                         'paypal_email']}),
        ('Address',{'fields':['address',
                              'city',
                              'state',
                              'zip_code']}),
        ('Configuration',{'fields':['active_season','default_location'],
                          'classes':['collapse']})    
    ]
    
    inlines = [LocationInline]

admin.site.register(Club,ClubAdmin)

