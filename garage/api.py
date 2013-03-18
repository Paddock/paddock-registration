
import json 

from django.core.urlresolvers import reverse

from tastypie import fields, api
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization,DjangoAuthorization
from tastypie.authentication import SessionAuthentication


from registration.models import Registration, Event, RaceClass, Car, \
    UserProfile, User, Coupon, Club, Season, Location, Membership, Group, \
    Result, Run, Session

from garage.api_auth import ClubAdminAuthorization, UserAdminAuthorization

v1_api = api.Api(api_name='v1')


class UserResource(ModelResource): 

    cars = fields.ToManyField('garage.api.CarResource', lambda b: b.obj.get_profile().cars,
                               full=True, null=True, blank=True, readonly=True)
    coupons = fields.ToManyField('garage.api.CouponResource', lambda b: b.obj.get_profile().coupons,
                                 full=True, null=True, blank=True, readonly=True)
    upcoming_events = fields.ToManyField('garage.api.EventResource',
                                         lambda bundle: bundle.obj.get_profile().get_next_events(), 
                                         blank=True, null=True, readonly=True, full=True)

    class Meta: 
        queryset = User.objects.all()
        resource_name = 'users'
        fields = ['first_name', 'last_name', 'email', 'username', 'cars',
                  'coupons', 'upcoming_events','id']
        resource_name = 'profile'  
        include_resource_uri = False
        authentication= SessionAuthentication()
        authorization = UserAdminAuthorization()


v1_api.register(UserResource())


class UserProfileResource(ModelResource):
    cars = fields.ToManyField('garage.api.CarResource', 'cars', full=True, 
        null=True, blank=True, readonly=True)
    coupons = fields.ToManyField('garage.api.CouponResource', 'coupons', 
        full=True, null=True, blank=True, readonly=True)
    user = fields.ToOneField('garage.api.UserResource', 'user', 'profile', full=True, readonly=True)
    upcoming_events = fields.ToManyField('garage.api.EventResource',
        lambda bundle: bundle.obj.get_next_events(), 
        blank=True, null=True, full=True, readonly=True)

    class Meta: 
        queryset = UserProfile.objects.all()
        resource_name = 'user_prof'
        excludes = ['activation_key']
        authentication= SessionAuthentication()
        #authorization= IsOwnerAuthorization()

    #todo: limit stuff here --> might need a resource where you can only see id... 
    #def apply_authorization_limits(self, request, object_list):
    #   return object_list.filter(user=request.user)


v1_api.register(UserProfileResource())



class CarResource(ModelResource):
    user_profile = fields.ToOneField(UserProfileResource, 'user_profile',blank=True,null=True)

    class Meta: 
        queryset = Car.objects.all()
        authentication= SessionAuthentication()
        #authorization = IsOwnerAuthorization() #TODO: Need to add permissions
        authorization = UserAdminAuthorization()
        fields = ['id', 'name', 'make', 'model', 'year', 'thumb', 'avatar',
         'provisional']
        always_return_data = True


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

    admins = fields.ToManyField('garage.api.UserResource', lambda b: b.obj.group.user_set, related_name="+", full=True, null=True, blank=True)
    
    class Meta:
        queryset = Club.objects.prefetch_related('seasons', 'locations', 'memberships')
        resource_name = 'club'
        authentication= SessionAuthentication()
        authorization = ClubAdminAuthorization()
        always_return_data = True


    #this seems horribly inefficient, but it won't happen that often
    def hydrate_admins(self, bundle): 
        admins = bundle.data['admins']
        bundle.obj.group = Group.objects.get(name="%s_admin"%bundle.obj.safe_name)
        if admins and not type(admins[0]) == type(bundle):  #dirty hack, because hydrate gets called twice
            users = User.objects.filter(username__in=[a['username'] for a in admins])
            for u in users: 
                bundle.obj.group.user_set.add(u)
        return bundle
        

v1_api.register(ClubResource())


class RaceClassResource(ModelResource): 

    club = fields.ToOneField('garage.api.ClubResource', 'club')
    default_pax_class = fields.ToOneField('garage.api.RaceClassResource', 'default_pax_class', blank=True, null=True, readonly=True)

    class Meta: 
        queryset = RaceClass.objects.all()
        resource_name = 'raceclass'
        authentication= SessionAuthentication()
        authorization = ClubAdminAuthorization()
        always_return_data = True

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
        authorization = ClubAdminAuthorization()
        excludes = ['_anon_f_name', '_anon_l_name']

    def dehydrate(self, bundle): 
        bundle.data['username'] = bundle.obj.user_prof.user.username
        bundle.data['real_name'] = '%s %s'%(bundle.obj.f_name, bundle.obj.l_name)
        return bundle

v1_api.register(MembershipResource())


class RunResource(ModelResource): 

    class Meta: 
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        queryset = Run.objects.all()

v1_api.register(RunResource())


class ResultResource(ModelResource):

    session = fields.CharField(readonly=True)
    runs = fields.ToManyField('garage.api.RunResource', 'runs', readonly=True, full=True)

    class Meta: 
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        queryset = Result.objects.all()
        include_resource_uri = False


    def dehydrate_session(self, bundle): 
        return bundle.obj.session.name


class RegistrationResource(ModelResource): 

    race_class = fields.ToOneField('garage.api.RaceClassResource', 'race_class', full=True)
    pax_class = fields.ToOneField('garage.api.RaceClassResource', 'pax_class', full=True, null=True, blank=True)
    bump_class = fields.ToOneField('garage.api.RaceClassResource', 'bump_class', full=True, null=True, blank=True)
    first_name = fields.CharField(attribute='first_name', readonly=True)
    last_name = fields.CharField(attribute='last_name', readonly=True)
    car_name = fields.CharField(attribute='car_name', readonly=True)

    results = fields.ToManyField('garage.api.ResultResource', 'results', readonly=True, full=True)

    class Meta: 
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        queryset = Registration.objects.all()
        excludes = ['_anon_l_name', '_anon_f_name', '_anon_car']

v1_api.register(RegistrationResource())


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
    club = fields.ToOneField('garage.api.ClubResource', 'club')
    club_name = fields.CharField(null=True, readonly=True)
    url = fields.CharField(null=True, readonly=True)

    class Meta: 
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        queryset = Event.objects.all()
        resource_name = "event"

    def dehydrate(self, bundle): 
        bundle.data['club_name'] = bundle.obj.season.club.name
        bundle.data['url'] = self.get_url(bundle)
        return bundle    


class EventDetailResource(EventResource): 

    regs = fields.ToManyField('garage.api.RegistrationResource', 
        attribute=lambda b: b.obj.get_results(), 
        full=True, readonly=True)
    sessions = fields.ToManyField('garage.api.SessionResource',
        attribute="sessions", full=True, readonly=True)

v1_api.register(EventDetailResource())


class SessionResource(ModelResource): 

    class Meta: 
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        queryset = Session.objects.all()
        resource_name = "sessions"

v1_api.register(SessionResource())


class SeasonResource(ModelResource):

    events = fields.ToManyField('garage.api.EventResource', 'events', 'season',
        full=True, null=True, blank=True, readonly=True)

    club = fields.ToOneField('garage.api.ClubResource', 'club')

    class Meta: 
        queryset = Season.objects.select_related().all()
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        always_return_data = True

    def save_m2m(self, bundle): 
        pass    

v1_api.register(SeasonResource())


class LocationResource(ModelResource): 
    
    club = fields.ToOneField('garage.api.ClubResource', 'club')

    class Meta: 
        queryset = Location.objects.all()
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()

v1_api.register(LocationResource())        


# No URI for these, so they don't need to be protected
class CouponResource(ModelResource):

    username = fields.CharField()

    club = fields.ToOneField('garage.api.ClubResource', 'club', 'season')
    #user_prof = fields.ToOneField('garage.api.UserProfileResource', 'user_prof', blank=True, null=True)

    class Meta: 
        queryset = Coupon.objects.prefetch_related().all()  
        authentication = SessionAuthentication()
        authorization = ClubAdminAuthorization()
        always_return_data = True

    def dehydrate(self, bundle):
        if bundle.obj.user_prof: 
            bundle.data['username'] = bundle.obj.user_prof.user.username
        else: 
            bundle.data['username'] = "N/A"
        return bundle    

    def hydrate_username(self, bundle): 
        username = bundle.data['username']
        if (not username) or (username == "N/A"): 
            bundle.object.user_prof = None

        else: 
            user = User.objects.get(username=username)
            bundle.obj.user_prof = user.get_profile()
        return bundle

v1_api.register(CouponResource())
