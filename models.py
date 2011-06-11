import os
import datetime
from urllib import pathname2url
import re

from django.db import models as m
from django.contrib.localflavor.us.forms import USStateField, USZipCodeField
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from django.contrib.auth.models import User

def urlsafe(name): 
    safe = re.sub(r'\s','',name)
    safe = pathname2url(safe)
    safe = safe.lower()    
    
    return safe
        
def find_driver_car(f_name=None,l_name=None,car_year=None,car_make=None,car_model=None):
    #look for a driver/car that might match any of these attrs
    raise NotImplementedError

class UserProfile(m.Model): 
    
    user = m.OneToOneField(User)
    
    address = m.CharField('Home Address',max_length=150)
    state = m.CharField('State',max_length=25)
    zip_code = m.CharField('Zip Code',max_length=13)
    
    def __unicode__(self): 
        return self.user.user_name
    
    def get_next_events(self): 
        today = datetime.datetime.today()
        #TODO: get all events that user is registered for, or that are comming up for clubs that you're member of   
        raise NotImplementedError
        
    
    def is_member(self,club): 
        today = datetime.datetime.today()
        for m in self.memberships: 
            if m.club == club and m.paid and m.valid_thru_date >= today: return m
        return False    
    
    def is_registered(self,event): 
        for r in self.registrations:
            if r.event == event: return r
        return False

class Club(m.Model):
    
    @property
    def name(self): 
	return self._name
    
    @name.setter
    def name(self,name): 
	self._name = name
	self.safe_name = urlsafe(name) 
	
    _name = m.CharField('Club Name',max_length=100)
    safe_name  = m.CharField("safe_name", max_length=100, primary_key=True) 
    
    created = m.DateTimeField(auto_now_add=True)
    last_mod = m.DateTimeField(auto_now=True)
    
    new_member_cost = m.DecimalField('New Membership Price', 
                                     max_digits = 100,
                                     decimal_places=2,
                                     default="0.00") 
    renew_cost = m.DecimalField('Membership Renewal Price', 
                                max_digits = 100,
                                decimal_places=2, default="0.00") 
    membership_terms = m.TextField('Membership Terms',blank=True)
               
    process_payments = m.BooleanField('Process Payments',default=True)
    paypal_email = m.CharField('Paypal Email Address',max_length=100,blank=True,
                               validators=[validate_email])
    
    address = m.CharField('Mailing Address',max_length=100,blank=True)
    city = m.CharField('City',max_length=100,blank=True)
    state = m.CharField('State',max_length=25,blank=True) #USStateField('State')
    zip_code = m.CharField('Zip Code',max_length=12,blank=True) #USZipCodeField('Zip Code')
    
    active_season = m.OneToOneField("Season",related_name="+",blank=True,null=True)
    default_location = m.OneToOneField("Location",related_name="+",blank=True,null=True)
    
    def __unicode__(self): 
	    return self.safe_name
	     

class Membership(m.Model): 
    
    num = m.IntegerField("ID #",null=True,default=None)
    
    start = m.DateField("Member Since")
    valid_thru = m.DateField("Valid Through")
    
    user = m.ForeignKey(User,related_name="memberships")
    club = m.ForeignKey("Club",related_name="memberships")
    
    _anon_f_name = m.CharField(max_length=50)
    _anon_l_name = m.CharField(max_length=50)
    
    def __unicode__(self):
        return "%s in %s>"%(self.user.username,self.club.safe_name)
    
    def clean(self): 
        pass
        #TODO: make the validate autoincrement num, if no num is provided
    
    @property    
    def f_name(self):
        if self.user: 
            return self.user.f_name
        return self._anon_f_name
            
    @property 
    def l_name(self): 
        if self.user: 
            return self.user.l_name
        return self._anon_l_name     
 
class RegType(m.Model):
    name = m.CharField("Name",max_length=20)
    class_letters = m.CharField("Class Letters",max_length=4)
    reg_limit = m.IntegerField("Registration Limit")
    index = m.FloatField("PAX multiplier")
    description = m.TextField("description")
    
    club = m.ForeignKey('Club',related_name="reg_types")
    
    def __unicode__(self): 
        return self.name
    
class RaceClass(m.Model): 
    name = m.CharField('Class Name',max_length=4)
    pax = m.FloatField('PAX multiplier')
    
    club = m.ForeignKey('Club',related_name='race_classes')
    
    def __unicode__(self): 
        return u"%s %1.3f"%(self.name,self.pax)
    
class Season(m.Model): 
    year = m.IntegerField(default=None)
    drop_lowest_events = m.IntegerField('# of Events to drop from points calculations',
                                        default=0)    
    
    club = m.ForeignKey('Club',related_name="seasons")
    
    def count_events_with_results(self): 
        return Event.objects.filter(season=self,regs__results__isnull=False).count() 
    def __unicode__(self): 
        return u"%d"%self.year
     
class Event(m.Model): 
    @property
    def name(self): 
	return self._name
    @name.setter
    def name(self,name): 
	self._name = name
	self.safe_name = urlsafe(name)
    
    _name = m.CharField('Name',max_length=40)
    safe_name = m.CharField(max_length=40)
    
    date = m.DateField('Event Date')
    
    reg_close = m.DateTimeField('Registration Close Date',blank=True,null=True)
    
    member_price = m.DecimalField("Price for club members", max_digits=10,
                                  decimal_places=2, default="0.00")
    non_member_price = m.DecimalField("Price for non club Members", max_digits=10, 
                                      decimal_places=2, default="0.00")
    non_pre_pay_penalty = m.DecimalField("Extra Cost if paying at the event", max_digits=10, 
                                         decimal_places=2, default="0.00")
    
    count_points = m.BooleanField("Include this event in season point totals",default=True)
    
    season = m.ForeignKey('Season',related_name="events",null=True,blank=True)    
    
    #TODO: modify on_delete to set to club default location
    location = m.ForeignKey('Location',blank=True,null=True,on_delete=m.SET_NULL)
    
    #This is to allow for registration of one event to automaticaly count toward any child events as well
    #TODO: Implement this, so that individual registrations are still created for each event
    child_events = m.ManyToManyField("Event",symmetrical=False,related_name="parent_events",
                                     blank=True,null=True,
                                     help_text="When drivers register for this event, they will automatically be" 
                                     "registered for all the associated events listed here.")
    
    #TODO: make a widget which knows how to render events, before registration closes
    #TODO: make a widget which knows how to render events, after registration closes
    
    def clean(self): 
	if self.reg_close.date() >= self.date: 
	    raise ValidationError("Registration must close before the date of the event.")
    
    def __unicode__(self): 
        return self.safe_name
        
class Registration(m.Model): 
    car = m.ForeignKey("Car",related_name="regs",blank=True,null=True)
    number = m.IntegerField("Car Number")
    race_class = m.ForeignKey("RaceClass",related_name="+")
    pax_class  = m.ForeignKey("RaceClass",related_name="+",blank=True,null=True)
    
    index_flag = m.BooleanField(default=False)
    total_raw_time = m.FloatField('Total Raw Time', blank=True, null=True, default = None)
    total_index_time = m.FloatField('Total Index Time', blank=True, null=True, default = None)
    
    class_points = m.IntegerField(blank=True,null=True)
    index_points = m.IntegerField(blank=True,null=True)
    
    #TODO: remove null
    event = m.ForeignKey("Event",related_name="regs")
    
    _anon_f_name = m.CharField(max_length=50,blank=True,null=True,default="N/A")
    _anon_l_name = m.CharField(max_length=50,blank=True,null=True,default="N/A")
    _anon_car = m.CharField(max_length=50,blank=True,null=True,default="N/A")
    
    #TODO: Remove Null
    user = m.ForeignKey(User,related_name="regs", blank=True, null=True)
    
    def __unicode__(self): 
        return self.user.username
    
    @property
    def car_name(self): 
	if not self.car is None: 
	    return "%d %s %s"%(self.car.year, self.car.make, self.car.model)
	return self._anon_car
    
    @property
    def first_name(self): 
        if self.user: 
            return self.user.first_name
        elif self._anon_f_name: 
            return self._anon_f_name
        return "Driver"
    
    @property
    def last_name(self):
        if self.user: 
            return self.user.last_name
        elif self._anon_l_name: 
            return self._anon_l_name
        return "Not On File"    
    @property
    def car_str(self): 
        if self.car: 
            pass
        elif self._anon_car: 
            return self._anon_car
        return "N/A"
    
class Session(m.Model): 
    name = m.CharField(max_length=30)
    event = m.ForeignKey("Event",related_name="sessions")
    course = m.OneToOneField("Course")
    
    def __unicode__(self): 
        return self.name
    
class Result(m.Model): 
    best_run = m.OneToOneField("Run",related_name="+",null=True)
    reg = m.ForeignKey("Registration",related_name="results")
    
    #session is used for database, so for clarity names sess
    #TODO: Remove null
    sess = m.ForeignKey("Session",related_name="results",null=True) 
    
    #TODO: make a widget so that a result knows how to render itslf, take options for class/index view
    
    def __unicode__(self): 
        return unicode(self.best_run)
    
    def calc_best_run(self): 
        br =  Run.objects.filter(result=self,result__runs__penalty__isnull=True).\
        order_by('calc_time')[0]
        self.best_run = br
        return br
        #return min(runs,key=lambda r:r.calc_time)

class Run(m.Model):     
    base_time = m.FloatField()
    calc_time = m.FloatField()
    index_time = m.FloatField()
    
    cones = m.IntegerField(default=0)
    penalty = m.CharField(default=None,max_length=10,null=True)
    
    result = m.ForeignKey("Result",related_name="runs")
    
    def set_times(self,base_time,cones): 
        self.base_time = base_time
        self.cones = cones
        
        self.calc_time = base_time+2.0*cones
        self.index_time = self.calc_time*self.result.reg.race_class.pax   
        
        return (self.calc_time,self.index_time)
        
    
    def __unicode__(self): 
        if self.penalty: 
            return self.penalty
        if self.cones: 
            return u"3.3f, +%d cones (3.3f)"%(self.calc_time,self.cones,self.index_time)
            
        return u"%3.3f(%3.3f)"%(self.calc_time,self.index_time)
    
class Location(m.Model):
    
    name = m.CharField('Location Name',max_length=100)
    safe_name = m.CharField(max_length=100)
    
    address = m.CharField('Address',max_length=250)
    
    lat = m.FloatField('Latitude')
    lon = m.FloatField('Longitude')
    
    club = m.ForeignKey('Club',related_name='locations')
    
    def __unicode__(self): 
        return self.safe_name
    
def upload_course_to(course,file_name): 
    return os.path.join(course.event.club.safe_name,course.event.safe_name,"")    
    
class Course(m.Model): 
    name = m.CharField('Name',max_length=50)
    safe_name = m.CharField(max_length=50)
    
    img_loc = m.ImageField('Course Drawing',upload_to=upload_course_to)
    
    event = m.ForeignKey('Event',related_name="courses")
    
    def __unicode__(self): 
        return self.safe_name
        
def uplaoad_car_to(car,file_name):
    return os.path.join(car.owner.username,"cars","")
    
class Car(m.Model): 
    name = m.CharField('Nickname',max_length=30)
    color = m.CharField('Color',max_length=40)
    year = m.IntegerField('Year')    
    make = m.CharField('Make',max_length=40)
    model = m.CharField('Model',max_length=40)
    
    
    avatar = m.ImageField('Picture of your car',upload_to=uplaoad_car_to)
    thumb = m.ImageField('Picture of your car',upload_to=uplaoad_car_to)
    
    owner = m.ForeignKey(User,related_name="cars")
    
    def __unicode__(self): 
    	return "%d %s %s"%(self.year,self.make,self.model)

        
class Lease(m.Model): 
    suggested_number = m.IntegerField("Suggested Number",null=True)
    suggested_race_class = m.ForeignKey('RaceClass',null=True,on_delete=m.SET_NULL,related_name='+')
    suggested_reg_type = m.ForeignKey('RegType',null=True,on_delete=m.SET_NULL,related_name="+")
    
    expiration = m.DateField("Expiration Date")
    permanent = m.BooleanField("Permanent Lease")
    
    user = m.ForeignKey(User,related_name="leases")
    car = m.ForeignKey("Car",related_name="leases")
    
    def __unicode__(self): 
        return "%s to %s"%(self.car.name ,self.user.username)