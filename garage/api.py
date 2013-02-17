from django.core.urlresolvers import reverse

from tastypie import fields, api
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization,DjangoAuthorization
from tastypie.authentication import SessionAuthentication

from registration.models import Registration, Event, RaceClass, Car, \
    UserProfile, User, Coupon, Club, Season, Location, Membership

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

    #todo: limit stuff here --> might need a resource where you can only see id... 
    #def apply_authorization_limits(self, request, object_list):
    #   return object_list.filter(user=request.user)


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
    seasons = fields.ToManyField('garage.api.SeasonResource', 'seasons', 'club', 
        full=True, readonly=True)
    locations = fields.ToManyField('garage.api.LocationResource', 'locations',
        'club', full=True, blank=True, null=True, readonly=True)
    memberships = fields.ToManyField('garage.api.MembershipResource', 
        'memberships', 'club', full=True, readonly=True)
    coupons = fields.ToManyField('garage.api.CouponResource', 'coupons', 
        full=True,  readonly=True)
    race_classes = fields.ToManyField('garage.api.RaceClassResource', 'race_classes', 
        full=True,  readonly=True)
    
    class Meta:
        queryset = Club.objects.prefetch_related('seasons', 'locations', 'memberships')
        resource_name = 'club'
        authentication= SessionAuthentication()
        authorization = Authorization()

v1_api.register(ClubResource())


class RaceClassResource(ModelResource): 

    club = fields.ToOneField('garage.api.ClubResource', 'club')
    default_pax_class = fields.ToOneField('garage.api.RaceClassResource', 'default_pax_class', blank=True, null=True)

    class Meta: 
        queryset = RaceClass.objects.all()
        resource_name = 'raceclass'
        authentication= SessionAuthentication()
        authorization = Authorization()

v1_api.register(RaceClassResource())


class MembershipResource(ModelResource):

    club = fields.ToOneField('garage.api.ClubResource', 'club')
    user_prof = fields.ToOneField('garage.api.UserProfileResource', 'user_prof')

    username = fields.CharField(readonly=True)
    real_name = fields.CharField(readonly=True)

    class Meta: 
        queryset = Membership.objects.all()
        authentication= SessionAuthentication()
        #authorization = IsOwnerAuthorization() #TODO: Need to add permissions
        authorization = Authorization()
        excludes = ['_anon_f_name', '_anon_l_name']

    def dehydrate(self, bundle): 
        bundle.data['username'] = bundle.obj.user_prof.user.username
        bundle.data['real_name'] = '%s %s'%(bundle.obj.f_name, bundle.obj.l_name)
        return bundle

v1_api.register(MembershipResource())        


class EventResource(ModelResource): 

    def get_url(self, bundle): 
        return reverse('registration.views.event',
            kwargs={'club_name': bundle.obj.season.club.safe_name,
            'season_year': bundle.obj.season.year,
            'event_name': bundle.obj.safe_name})

    name = fields.CharField(attribute='name')
    date = fields.DateField(attribute='date')
    location = fields.ToOneField('garage.api.LocationResource', 'location', 
        blank=True, null=True)
    season = fields.ToOneField('garage.api.SeasonResource', 'season')
    club_name = fields.CharField(null=True, readonly=True)
    url = fields.CharField(null=True, readonly=True)

    class Meta: 
        authentication = SessionAuthentication()
        authorization = Authorization()
        queryset = Event.objects.all()

    def dehydrate(self, bundle): 
        bundle.data['club_name'] = bundle.obj.season.club.name
        bundle.data['url'] = self.get_url(bundle)
        return bundle    
  

v1_api.register(EventResource())


class SeasonResource(ModelResource):

    events = fields.ToManyField('garage.api.EventResource', 'events', 'season',
        full=True, null=True, blank=True, readonly=True)

    club = fields.ToOneField('garage.api.ClubResource', 'club', 'season')

    class Meta: 
        queryset = Season.objects.prefetch_related().all()
        authentication = SessionAuthentication()
        authorization = Authorization()
        always_return_data = True

    def save_m2m(self, bundle): 
        pass    

v1_api.register(SeasonResource())


class LocationResource(ModelResource): 

    class Meta: 
        queryset = Location.objects.all()

v1_api.register(LocationResource())        


# No URI for these, so they don't need to be protected
class CouponResource(ModelResource):

    username = fields.CharField(readonly=True)

    club = fields.ToOneField('garage.api.ClubResource','club','season')
    user_prof = fields.ToOneField('garage.api.UserProfileResource', 'user_prof', blank=True, null=True)


    class Meta: 
        queryset = Coupon.objects.prefetch_related().all()  
        authentication = SessionAuthentication()
        authorization = Authorization()

    def dehydrate(self, bundle):
        print "TESTING: ", type(bundle.obj.user_prof)
        if bundle.obj.user_prof: 
            bundle.data['username'] = bundle.obj.user_prof.user.username
        else: 
            bundle.data['username'] = "N/A"
        return bundle     

v1_api.register(CouponResource())

