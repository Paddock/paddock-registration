from django.core.urlresolvers import reverse

from tastypie import fields, api
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization,DjangoAuthorization
from tastypie.authentication import SessionAuthentication

from registration.models import Registration, Event, RaceClass, Car, \
    UserProfile, User, Coupon, Club, Season, Location

v1_api = api.Api(api_name='v1')


class UserResource(ModelResource): 
    class Meta: 
        queryset = User.objects.all()
        resource_name = 'users'
        fields = ['first_name', 'last_name', 'email', 'username']
        include_resource_uri = False

#v1_api.register(UserResource())


class UserProfileResource(ModelResource):
    cars = fields.ToManyField('garage.api.CarResource', 'cars', full=True, 
        null=True, blank=True)
    coupons = fields.ToManyField('garage.api.CouponResource', 'coupons', 
        full=True, null=True, blank=True)
    user = fields.ToOneField('garage.api.UserResource', 'user', 'profile', full=True)
    upcoming_events = fields.ToManyField('garage.api.EventResource',
        lambda bundle: bundle.obj.get_next_events(), 
        blank=True, null=True, readonly=True, full=True)

    class Meta: 
        queryset = UserProfile.objects.all()
        resource_name = 'profile'
        excludes = ['activation_key']
        authentication= SessionAuthentication()
        #authorization= IsOwnerAuthorization()
        authorization = Authorization()

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)
    

v1_api.register(UserProfileResource())


class CarResource(ModelResource):
    #user = fields.ToOneField(UserResource, 'user_profile',blank=True,null=True)

    class Meta: 
        queryset = Car.objects.all()
        authentication= SessionAuthentication()
        #authorization = IsOwnerAuthorization() #TODO: Need to add permissions
        authorization = Authorization()
        fields = ['id', 'name', 'make', 'model', 'year', 'thumb', 'avatar',
         'provisional']
        always_return_data = True

    def obj_create(self, bundle, request=None, **kwargs):
        return super(CarResource, self).obj_create(bundle, request, user_profile=request.user.get_profile())

v1_api.register(CarResource()) 


class ClubResource(ModelResource):

    name = fields.CharField(attribute='name')
    #active_season = fields.ToOneField('garage.api.SeasonResource', 'active_season', 
    #    'club', full=True, blank=True, null=True)
    seasons = fields.ToManyField('garage.api.SeasonResource', 'seasons', 'club', full=True)
    locations = fields.ToManyField('garage.api.LocationResource', 'locations', 
        'club', full=True , blank=True, null=True)
    class Meta:
        queryset = Club.objects.all()
        resource_name = 'club'

v1_api.register(ClubResource())

class EventResource(ModelResource): 

    def get_url(self,bundle): 
        return reverse('registration.views.event',
            kwargs={'club_name': bundle.obj.season.club.safe_name,
            'season_year': bundle.obj.season.year,
            'event_name': bundle.obj.safe_name})

    name = fields.CharField(attribute='name')
    date = fields.DateField(attribute='date')
    location = fields.ToOneField('garage.api.LocationResource', 'location', 
        blank=True, null=True)
    season = fields.ToOneField('garage.api.SeasonResource','season')
    club_name = fields.CharField(null=True,readonly=True)
    url = fields.CharField(null=True,readonly=True)

    class Meta: 
        authentication = SessionAuthentication()
        authorization = Authorization()
        queryset = Event.objects.select_related().all()

    def dehydrate(self,bundle): 
        bundle.data['club_name'] = bundle.obj.season.club.name
        bundle.data['url'] = self.get_url(bundle)
        return bundle    
  

v1_api.register(EventResource())


class SeasonResource(ModelResource):

    events = fields.ToManyField('garage.api.EventResource','events','season',
        full=True,null=True,blank=True)

    club = fields.ToOneField('garage.api.ClubResource','club','season')

    class Meta: 
        queryset = Season.objects.all()
        authentication = SessionAuthentication()
        authorization = Authorization()
        always_return_data = True

    def save_m2m(self,bundle): 
        pass    

v1_api.register(SeasonResource())

class LocationResource(ModelResource): 

    class Meta: 
        queryset = Location.objects.all()

v1_api.register(LocationResource())        

# No URI for these, so they don't need to be protected
class CouponResource(ModelResource):

    class Meta: 
        queryset = Coupon.objects.all()  
        allowed_methods = ['get']








