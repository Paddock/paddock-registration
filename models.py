import os
import datetime
from urllib import pathname2url
import re
from copy import copy

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
        
def find_user(query):
    """look for a driver that might match any of these attrs"""
    
    return User.objects.filter(m.Q(last_name__icontains=query)|
                                 m.Q(first_name__icontains=query)).all()

class TodayOrLaterField(m.DateField): 
    def validate(self,value,model_instance): 
	super(TodayOrLaterField,self).validate(value,model_instance)
	
	if value and value < datetime.date.today()+datetime.timedelta(days=1):
	    raise ValidationError("Coupon must expire atleast one day from now")

class CouponCodeField(m.CharField): 
    def validate(self,value,model_instance): 
	super(CouponCodeField,self).validate(value,model_instance)
	
	if " " in value: 
	    raise ValidationError("Spaces not allowed in the code")
	

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
                                     max_digits = 10,
                                     decimal_places=2,
                                     default="0.00") 
    renew_cost = m.DecimalField('Membership Renewal Price', 
                                max_digits = 10,
                                decimal_places=2, default="0.00") 
    membership_terms = m.TextField('Membership Terms',blank=True)
               
    process_payments = m.BooleanField('Process Payments',default=True)
    paypal_email = m.CharField('Paypal Email Address',max_length=100,blank=True,
                               validators=[validate_email])
    
    address = m.CharField('Mailing Address',max_length=100,blank=True)
    city = m.CharField('City',max_length=100,blank=True)
    state = m.CharField('State',max_length=25,blank=True) #USStateField('State')
    zip_code = m.CharField('Zip Code',max_length=12,blank=True) #USZipCodeField('Zip Code')
    
    events_for_dibs = m.IntegerField("# of events to get dibs",default=3)
    
    active_season = m.OneToOneField("Season",related_name="+",blank=True,null=True)
    default_location = m.OneToOneField("Location",related_name="+",blank=True,null=True)
    
    def __unicode__(self): 
	    return self.safe_name
	
    def assign_dibs(self):
	"""looks through the most recent events to assign 
	dibs to anyone who has earned it.""" 
        today = datetime.date.today()
	#find last N events
	try: 
	    recent_events = Event.objects.filter(season__club=self,
	                                         sessions__isnull=False,
	                                         sessions__results__isnull=False
	                                         ).\
	                                  order_by('-date').all()[:self.events_for_dibs].annotate(m.Count("sessions"))
	    #TODO: Look into aggregation to try and avoid the raw query here, 
	    #      but the raw query migh be the most efficient
	    """recent_events = [x for x in Event.objects.raw('''SELECT "paddock_event".* FROM "paddock_event" 
	                                      INNER JOIN "paddock_session" ON 
	                                      ("paddock_event"."id" = "paddock_session"."event_id") 
	                                      INNER JOIN "paddock_result" ON (
	                                      "paddock_session"."id" = "paddock_result"."session_id") 
	                                      INNER JOIN "paddock_season" ON 
	                                      ("paddock_event"."season_id" = "paddock_season"."id") 
	                                      WHERE ("paddock_result"."id" IS NOT NULL 
	                                             AND "paddock_season"."club_id" = "%s"  
	                                            AND "paddock_session"."id" IS NOT NULL) 
	                                      GROUP BY "paddock_event"."id"
	                                      ORDER BY "paddock_event"."date" DESC
	                                      LIMIT %d'''%(self.pk,self.events_for_dibs))]"""
            print "recent_events:", recent_events
	    if len(recent_events) != self.events_for_dibs: 
		#there have not been enough events yet to grant dibs
		return 
	    
	except Event.DoesNotExist: #then there are no events, so just stop 
	    return 
	
        #look for all dibs with drivers who have a registration in one of the last N events
        try: 
	    """regs=Registration.objects.select_related("reg_detail__user",
	                                             'reg_detail__user__dibs').\
	                         filter(event__in=recent_events,
	                                reg_detail__user__dibs__isnull=False,
		                        ).values('reg_detail__user','number','race_class').\
		        annotate(reg_count = m.Count('pk')).filter(reg_count__gte=1).all()"""
	    regs=Registration.objects.select_related("reg_detail__user",
	                                             'reg_detail__user__dibs').\
	                          filter(event__in=recent_events,
		                        ).all()
	    print regs
	except Registration.DoesNotExist: #No one meets the criteria, so just stop
	    return 	
	for reg in regs: 
	    dibs = reg.reg_detail.user.dibs.all()
	    time_held = dibs.expires-dibs.created
	    months_held = time_held.days/30 #gets the whole number of months held, drops remainder
	    if months_held > 12: 
		months_held = 12 #can't hold for more than 1 year
	    dibs.duration = months_held
	    dibs.expires = reg.event.date+datetime.timedelta(days=months_held*30)
	    dibs.save()
	
	#check for new users who earned dibs
	#look for people who have used the same num/class in the last N events    
	try: 
	    regs=Registration.objects.select_related("reg_detail__user",
	                                             "race_class").\
	                         filter(event__in=recent_events,
		                        ).values('reg_detail__user','number','race_class').\
		        annotate(reg_count = m.Count('pk')).filter(reg_count=self.events_for_dibs).get()
	except Registration.DoesNotExist: #No one meets the criteria, so just stop
	    return 
	
	try: 
	    next_event = Events.objects.filter(season_club=self,date__gt=today).order_by('date')[0].get()
	    #get dibs for one month past the date of the next event
	    duration = datetime.timedelta(days=30)
	    expires =  next_event.date + duration
	except Event.DoesNotExist: 
	    #if there is no future even in the system yet, just give it to you for 6 months
	    duration = datetime.date.today()+datetime.timedelta(days=180)
	    expires = today+datetime.timedelta(days=180)
	
	#get or create because someone with dibs might have run the last X events and be in this list
	for reg in regs: 
	    user = reg.reg_detail.user
	    dibs,created = Dibs.objects.get_or_create(number=reg.number,
	                        race_class=reg.race_class,
	                        club=self,
	                        user=user, 
	                        default={'expires':expires,'duration':duration})
		
	
	
    def check_dibs(self,number,race_class): 
	"""Checks to see if anyone has dibs on the given number/race_class for a club.
        returns True if someone has dibs on the number/race_class
        """
	
	try: 
            if isinstance(race_class,str): 
		Dibs.objects.filter(club=self,number=number,race_class__name=race_class).get()
	    else: 	
		Dibs.objects.filter(club=self,race_class=race_class,number=number).get()
        except Dibs.DoesNotExist: 
	    return False
	return True     

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
    
    def clean(self): 
	try: 
	    Membership.objects.filter(club=self.club,num=self.num).get()
	except Membership.DoesNotExist: 
	    pass
	else: 
	    raise ValidationError("A member with that number already exists")
    
    def save(self): 
	if not self.num:
	    try: 
		Membership.objects.filter(club==self.club, num__max).get()
	    except Membership.leNotExist: 
		self.num = 100
		
	super(Membership,self).save()
 

class RaceClass(m.Model): 
    name = m.CharField('Class Name',max_length=4)
    pax = m.FloatField('PAX multiplier')
    
    pax_class = m.BooleanField('PAX Class',default=False)
    description = m.TextField("Description",blank=True,default="")
    user_reg_limit = m.IntegerField("Limit for Users",null=True,default=None)
    event_reg_limit = m.IntegerField("Limit per EVent",null=True,default=None)
    
    club = m.ForeignKey('Club',related_name='race_classes')
    
    def __unicode__(self): 
        return u"%s %1.3f"%(self.name,self.pax)
    
class Dibs(m.Model): 
    created = m.DateField(auto_now_add=True)
    expires = m.DateField("Expires")
    duration = m.IntegerField("#of days",
                              help_text="# of days after the most recent event a User ran in the Dibs is valid for")
    number = m.IntegerField("Number")    
    race_class = m.ForeignKey('RaceClass',related_name='+')
    club = m.ForeignKey("Club",related_name='dibs')
    user = m.ForeignKey(User,related_name='dibs')
    
    
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
    
    season = m.ForeignKey('Season',related_name="events")    
    
    #TODO: modify on_delete to set to club default location
    location = m.ForeignKey('Location',blank=True,null=True,on_delete=m.SET_NULL)
    
    #This is to allow for registration of one event to automaticaly count toward any child events as well
    #TODO: Implement this, so that individual registrations are still created for each event
    child_events = m.ManyToManyField("self",symmetrical=False,related_name="parent_events",
                                     blank=True,null=True,
                                     help_text="When drivers register for this event, they will automatically be" 
                                     "registered for all the associated events listed here.")
    
    #TODO: make a widget which knows how to render events, before registration closes
    #TODO: make a widget which knows how to render events, after registration closes
    
    def allow_number_race_class(self,number,race_class): 
	"""Checks to see if the specified number and race_class are available for this event"""
        #check if the number/class is used in this event 
        reg_check = Event.objects.filter(id=self.id,
                             regs__number=number,	                     
	                     regs__race_class=race_class).count()
	if reg_check: 
	    return False
	
	#Check if the number/class is used in any child events
	for event in self.child_events.all(): 
	    reg_check = Event.objects.filter(id=event.id,
	                                     regs__number=number,	                     
	                                     regs__race_class=race_class).count()
	    
	    if reg_check: 
		return False
	    
	if self.season.club.check_dibs(number,race_class): 
	    return False
        return True	
    
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
    
    event = m.ForeignKey("Event",related_name="regs")
    
    reg_detail = m.ForeignKey("RegDetail",related_name="regs",blank=True,null=True)
    
    @property
    def user(self):
	return self.reg_detail.user
    
    #used only for anonymous regs
    _anon_f_name = m.CharField(max_length=50,blank=True,null=True,default="N/A")
    _anon_l_name = m.CharField(max_length=50,blank=True,null=True,default="N/A")
    _anon_car = m.CharField(max_length=50,blank=True,null=True,default="N/A")
    
    @property
    def car_name(self): 
	if not self.car is None: 
	    return "%d %s %s"%(self.car.year, self.car.make, self.car.model)
	return self._anon_car
    
    
    @property
    def first_name(self): 
        if self.reg_detail: 
            return self.reg_detail.user.first_name
        elif self._anon_f_name: 
            return self._anon_f_name
        return "Driver"
    
    @property
    def last_name(self):
        if self.reg_detail: 
            return self.user.last_name
        elif self._anon_l_name: 
            return self._anon_l_name
        return "Not On File" 
    
    def __unicode__(self):
	if self.reg_detail: 
	    return "%s for %s"%(self.reg_detail.user.username,self.event.name)
	return "anon: %s %s for %s"%(self.first_name,self.last_name,self.event.name)
    
    def associate_with_user(self,user): 
	self._anon_f_name = "N/A"
	self._anon_l_name = "N/A"
	self.reg_detail = RegDetail()
	self.reg_detail.user = user
    
    def clean(self): 
	if not self.event.allow_number_race_class(self.number,self.race_class):
	    raise ValidationError('%d %s is already taken, pick another number.'%(self.number,self.race_class.name))
	
	#if necessary, check to make sure user has not already run the max times in this class
        if self.reg_detail and self.race_class.user_reg_limit:	
	    reg_count = Registration.objects.filter(event__season__club=self.event.season.club,
	                                            reg_detail__user=self.reg_detail.user,
	                                            reg_detail__isnull=False,
	                                            race_class=self.race_class).count()
	    if reg_count >= self.race_class.user_reg_limit:
		raise ValidationError("You have reached the registration limit for %s."%self.race_class.name)
	        
	#TODO: Check if Event has reached the maximum number of allowed regs in this reg class
	if self.race_class.event_reg_limit: 
	    reg_count = Registration.objects.filter(event=self.event).count()
	    if reg_count >= self.race_class.event_reg_limit: 
		raise ValidationError("Only %d registrations for %s are allowed "
		                      "for this event. The class is full"%(self.race_class.event_reg_limit,
		                                                           self.race_class.name))
	                                            
        
class RegDetail(m.Model): 
    
    user = m.ForeignKey(User,related_name="regs")
    #TODO: transaction = m.ForeignKey("Transaction",related_name="+")
    
    def __unicode__(self): 
        return self.user.username   

    
class Session(m.Model): 
    name = m.CharField(max_length=30)
    event = m.ForeignKey("Event",related_name="sessions")
    course = m.OneToOneField("Course",blank=True,null=True)
    
    def __unicode__(self): 
        return self.name
    
class Result(m.Model): 
    best_run = m.OneToOneField("Run",related_name="+",null=True)
    reg = m.ForeignKey("Registration",related_name="results")
    
    #TODO: Remove null
    session = m.ForeignKey("Session",related_name="results",null=True) 
    
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
    base_time = m.FloatField('Base Time')
    calc_time = m.FloatField('Calculated Time')
    index_time = m.FloatField('Indexed Time')
    
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
    
    @property
    def car_str(self): 
	return "%s %s %s"%(self.year,self.make,self.model)   
	
    
    def __unicode__(self): 
    	return "%d %s %s"%(self.year,self.make,self.model)

        
class Lease(m.Model): 
    suggested_number = m.IntegerField("Suggested Number",null=True)
    suggested_race_class = m.ForeignKey('RaceClass',null=True,on_delete=m.SET_NULL,related_name='+')
    
    expiration = m.DateField("Expiration Date")
    permanent = m.BooleanField("Permanent Lease")
    
    user = m.ForeignKey(User,related_name="leases")
    car = m.ForeignKey("Car",related_name="leases")
    
    def __unicode__(self): 
        return "%s to %s"%(self.car.name ,self.user.username)
    
class Transaction(m.Model): 
    token = m.CharField("Token",max_length=50,blank=True,null=True)
    payer_id = m.CharField("Payer #",max_length=50,blank=True,null=True)
    transaction_id = m.CharField("Transac. #",max_length=50,blank=True,null=True)
    price = m.DecimalField("$", max_digits=10, decimal_places=2, default = "0.00")
    
    created = m.DateTimeField(auto_now_add=True)
    completed = m.DateTimeField(blank=True,null=True)
    
    #coupon_id = Column(Integer,ForeignKey('pdk_coupon.id'))
    #coupon = relationship("Coupon",backref=backref("transaction", uselist=False))
    
class Coupon(m.Model):     
    code = CouponCodeField("code",max_length=20)
    
    is_percent = m.BooleanField("%",default=False)   
    is_giftcard = m.BooleanField("GiftCard",default=False)
    permanent = m.BooleanField("permanent",default=False)
    single_use_per_user = m.BooleanField("Once per user", default=False)
    
    discount_amount = m.DecimalField("$ discount",
                                     max_digits=10,
                                     decimal_places=2,
                                     default = "0.00")
    uses_left = m.IntegerField("# uses",default=1)
    expires = TodayOrLaterField(blank=True,default=None)
    
    def clean(self): 
	pass
	
    
    #user_id = Column(Integer,ForeignKey("tg_user.user_id"))
    #club_id = Column(Integer,ForeignKey("pdk_club.club_id"))    