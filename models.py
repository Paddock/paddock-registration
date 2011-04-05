import os
import datetime

from django.db import models as m
from django.contrib.localflavor.us.forms import USStateField, USZipCodeField

from django.contrib.auth.models import User


def find_driver_car(f_name=None,l_name=None,car_year=None,car_make=None,car_model=None):
    #look for a driver/car that might match any of these attrs
    raise NotImplementedError

class UserProfile(m.Model): 
    
    user = m.OneToOneField(User)
    
    address = m.CharField('Home Address',max_length=150)
    state = m.CharField('State',max_length=25)
    zip_code = m.CharField('Zip Code',max_length=13)
    
    def __repr__(self): 
        return "<Driver: %s>"%self.user.user_name
    
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
    
    club_name = m.CharField('Club Name',max_length=100)
    safe_name  = m.CharField(max_length=100) 
    
    created = m.DateTimeField(auto_now_add=True)
    last_mod = m.DateTimeField(auto_now=True)
    
    new_member_cost = m.DecimalField('New Membership Price', max_digits = 100,decimal_places=2, default=0.0) 
    renew_cost = m.DecimalField('Membership Renewal Price', max_digits = 100,decimal_places=2, default=0.0) 
    membership_terms = m.TextField('Membership Terms')
               
    process_payments = m.BooleanField('Process Payments',default=True)
    paypal_email = m.CharField('Paypal Email Address',max_length=100)
    
    address = m.CharField('Mailing Address',max_length=100)
    city = m.CharField('City',max_length=100)
    state = m.CharField('State',max_length=25) #USStateField('State')
    zip_code = m.CharField('Zip Code',max_length=12) #USZipCodeField('Zip Code')
    
    active_season = m.OneToOneField("Season",related_name="+")
    default_location = m.OneToOneField("Location",related_name="+")
    
    def clean(self): 
        #TODO: set the safe_name from the name using a shared safing function
        #TODO: Create the admin group, and the appropriate conditions
        raise NotImplementedError
    
    def __unicode__(self): 
	return "<Club: %s>"%self.safe_name

class Membership(m.Model): 
    
    num = m.IntegerField("ID #",null=True,default=None)
    
    start = m.DateField("Member Since")
    valid_thru = m.DateField("Valid Through")
    
    user_prof = m.ForeignKey('UserProfile',related_name="memberships")
    club = m.ForeignKey("Club",related_name="memberships")
    
    _anon_f_name = m.CharField(max_length=50)
    _anon_l_name = m.CharField(max_length=50)
    
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
    
class RaceClass(m.Model): 
    name = m.CharField('Class Name',max_length=4)
    pax = m.FloatField('PAX multiplier')
    
    club = m.ForeignKey('Club',related_name='race_classes')
    
class Season(m.Model): 
    year = m.DateField()
    drop_lowest_events = m.IntegerField('# of Events to drop from points calculations')    
    
    club = m.ForeignKey('Club',related_name="seasons")
     
class Event(m.Model): 
    name = m.CharField('Name',max_length=40)
    safe_name = m.CharField(max_length=40)
    
    date = m.DateField('Event Date') #TODO: validate that this date is at least today or later
    reg_close = m.DateTimeField('Registration Close Date') #TODO: validate that this is no later than the event date
    
    member_price = m.DecimalField("Price for club members", max_digits=10,decimal_places=2, default=0.0)
    non_member_price = m.DecimalField("Price for non club Members", max_digits=10, decimal_places=2, default=0.0)
    non_pre_pay_penalty = m.DecimalField("Extra Cost if paying at the event", max_digits=10, decimal_places=2, default=0.0)
    
    count_points = m.BooleanField("Include this event in season point totals",default=True)
    
    #TODO: modify on_delete to set to club default location
    location = m.ForeignKey('Location',null=True,on_delete=m.SET_NULL)
    
    #This is to allow for registration of one event to automaticaly count toward any child events as well
    #TODO: Implement this, sot that individual registrations are still created for each event
    child_events = m.ManyToManyField("Event",symmetrical=False,related_name="parent_events",
                                     help_text="When drivers register for this event, they will automatically be" 
                                     "registered for all the associated events listed here.")
    
    #TODO: make a widget which knows how to render events, before registration closes
    #TODO: make a widget which knows how to render events, after registration closes
    
class Registration(m.Model): 
    car = m.ForeignKey("Car",related_name="regs")
    number = m.IntegerField("Car Number")
    race_class = m.ForeignKey("RaceClass",related_name="+")
    reg_type = m.ForeignKey("RegType",related_name="+")
    
    index_flag = m.BooleanField(default=False)
    total_raw_time = m.FloatField('Total Raw Time')
    total_index_time = m.FloatField('Total Index Time')
    
    class_points = m.IntegerField()
    index_points = m.IntegerField()
    
    event = m.ForeignKey("Event",related_name="regs")
    
    _anon_f_name = m.CharField(max_length=50)
    _anon_l_name = m.CharField(max_length=50)
    _anon_car = m.CharField(max_length=50)
    
    user = m.ForeignKey("UserProfile",related_name="regs")
    
    @property
    def first_name(self): 
        if self.user: 
            return self.user.f_name
        elif self._anon_f_name: 
            return self._anon_f_name
        return "Driver"
    
    @property
    def last_name(self):
        if self.user: 
            return self.user.l_name
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
    
class Result(m.Model): 
    best_run = m.OneToOneField("Run",related_name="+")
    reg = m.ForeignKey("Registration",related_name="results")
    
    #session is used for database, so for clarity names sess
    sess = m.ForeignKey("Session",related_name="results") 
    
    #TODO: make a widget so that a result knows how to render itslf, take options for class/index view
    
    def find_best_run(self): 
        pass
        #TODO: search the runs, and pick the best one to be the best_run attr

class Run(m.Model):     
    base_time = m.FloatField()
    calc_time = m.FloatField()
    index_time = m.FloatField()
    
    cones = m.IntegerField(default=0)
    penalty = m.CharField(max_length=10)
    
    result = m.ForeignKey("Result",related_name="runs")
    
class Location(m.Model):
    
    name = m.CharField('Location Name',max_length=100)
    safe_name = m.CharField(max_length=100)
    
    address = m.CharField('Address',max_length=250)
    
    lat = m.FloatField('Latitude')
    lon = m.FloatField('Longitude')
    
    club = m.ForeignKey('Club',related_name='locations')
    
def upload_course_to(course,file_name): 
    return os.path.join(course.event.club.safe_name,course.event.safe_name,"")    
    
class Course(m.Model): 
    name = m.CharField('Name',max_length=50)
    safe_name = m.CharField(max_length=50)
    
    img_loc = m.ImageField('Course Drawing',upload_to=upload_course_to)
    
    event = m.ForeignKey('Event',related_name="courses")
    

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
    
    owner = m.ForeignKey('UserProfile',related_name="cars")
    
    def __unicode__(self): 
    	return "<Car: %d %s %s>"%(int(self.year),self.make,self.model)

        
class Lease(m.Model): 
    suggested_number = m.IntegerField("Suggested Number",null=True)
    suggested_race_class = m.ForeignKey('RaceClass',null=True,on_delete=m.SET_NULL,related_name='+')
    suggested_reg_type = m.ForeignKey('RegType',null=True,on_delete=m.SET_NULL,related_name="+")
    
    expiration = m.DateField("Expiration Date")
    permanent = m.BooleanField("Permanent Lease")
    
    user = m.ForeignKey("UserProfile",related_name="leases")
    car = m.ForeignKey("Car",related_name="leases")
    
    def __unicode__(self): 
	return "<Lease: %s to %s>"%(unicode(self.car),self.user.username)