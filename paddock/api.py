from tastypie import fields, api
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization, DjangoAuthorization

from paddock.models import Registration, Event, RaceClass

v1_api = api.Api(api_name='v1')

class EventResource(ModelResource): 
    regs = fields.ToManyField('paddock.api.RegistrationResource','regs')
    
    class Meta: 
        queryset = Event.objects.select_related('regs','season').all()
v1_api.register(EventResource())

class RaceClassResource(ModelResource): 
    
    class Meta: 
        queryset = RaceClass.objects.all()
v1_api.register(RaceClassResource())


class RegistrationResource(ModelResource):
    event = fields.ToOneField(EventResource,'event')
    race_class = fields.ToOneField(RaceClassResource,'race_class')
    bump_class = fields.ToOneField(RaceClassResource,'bump_class',null=True)
    pax_class = fields.ToOneField(RaceClassResource,'pax_class',null=True)
    
    
    class Meta:
        queryset = Registration.objects.all()
        excludes = ['_anon_car', '_anon_f_name', '_anon_l_name']
        authorization = Authorization() #TODO: Need to add permissions
    
    def dehydrate(self,bundle): 
        bundle.data['first_name'] = bundle.obj.first_name
        bundle.data['last_name'] = bundle.obj.last_name
        bundle.data['car_name'] = bundle.obj.car_name
        bundle.data['user'] = bundle.obj.user.username
        
        return bundle
v1_api.register(RegistrationResource())
        
        
        
        
