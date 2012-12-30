from tastypie import fields, api
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization,DjangoAuthorization
from tastypie.authentication import SessionAuthentication

from registration.models import Registration, Event, RaceClass, Car, UserProfile, User, Coupon

v1_api = api.Api(api_name='v1')


class UserResource(ModelResource): 
    class Meta: 
        queryset = User.objects.all()
        resource_name = 'users'
        fields = ['first_name','last_name','email','username']
        include_resource_uri = False

#v1_api.register(UserResource())


class UserProfileResource(ModelResource):
    cars = fields.ToManyField('garage.api.CarResource', 'cars', full=True,null=True,blank=True)
    coupons = fields.ToManyField('garage.api.CouponResource', 'coupons',full=True,null=True,blank=True)
    user = fields.ToOneField('garage.api.UserResource', 'user', 'profile',full=True)

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
        fields = ['id','name','make','model','year','thumb','avatar']
        always_return_data = True

    def obj_create(self, bundle, request=None, **kwargs):
        return super(CarResource, self).obj_create(bundle, request, user_profile=request.user.get_profile())

v1_api.register(CarResource())    


class CouponResource(ModelResource):

    class Meta: 
        queryset = Coupon.objects.all()  
        allowed_methods = ['get']
v1_api.register(CouponResource())    
