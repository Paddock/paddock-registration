import os
import datetime
from urllib import pathname2url
import re
from copy import copy
import hashlib
import random

from django.db import models as m
from django.contrib.localflavor.us.forms import USStateField, USZipCodeField
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from django.template.loader import render_to_string

from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.conf import settings 

#TODO: need to replace this with some sort of plugin system
from paddock.points_calculators.nora_class_points import calc_points as class_points
from paddock.points_calculators.nora_index_points import calc_points as index_points



def urlsafe(name): 
    safe = re.sub(r'\s','',name)
    safe = pathname2url(safe)
    safe = safe.lower()    

    return safe

def find_user(query):
    """look for a driver that might match any of these attrs"""

    return User.objects.filter(m.Q(last_name__icontains=query)|
                               m.Q(first_name__icontains=query)|
                               m.Q(username__icontains=query)).all()

def clean_dibs(): 
    for c in Club.objects.all(): 
        c.assign_dibs()

    Dibs.objects.filter(expires__lt=datetime.date.today()).delete()	

class TodayOrLaterField(m.DateField): 
    def validate(self,value,model_instance): 
        super(TodayOrLaterField,self).validate(value,model_instance)

        if value and value < datetime.date.today()+datetime.timedelta(days=1):
            raise ValidationError("Date must be at least one day from now")

class CouponCodeField(m.CharField): 
    def validate(self,value,model_instance): 
        super(CouponCodeField,self).validate(value,model_instance)

        if " " in value: 
            raise ValidationError("Spaces not allowed in the code")

class UserProfile(m.Model): 
    
    user = m.OneToOneField(User)
    
    activation_key = m.CharField('activation key', max_length=40)
        
    address = m.CharField('Home Address',max_length=150,null=True,blank=True)
    city = m.CharField('City',max_length=25,null=True,blank=True)
    state = m.CharField('State',max_length=25,null=True,blank=True)
    zip_code = m.CharField('Zip Code',max_length=13,null=True,blank=True)    
    
    def __unicode__(self):
        return u"User profile for %s" % self.user    
    
    def send_activation_email(self): 
        
        print self.user.first_name
        
        ctx_dict = {'activation_key': self.activation_key,
                    'SITE_URL': settings.SITE_URL,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'user':self.user}
        subject = render_to_string('paddock/activation_email_subject.txt',
                                   ctx_dict)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string('paddock/activation_email.txt',
                                   ctx_dict)
        
        self.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)        

    def get_next_events(self): 
        today = datetime.datetime.today()
        #TODO: get all events that user is registered for, 
        #      or that are coming up for clubs that you're member of   
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
    
#causes creation of user profile just after new users are created    
def create_user_profile(sender, instance, created, **kwargs): 
    if created:
        p = UserProfile.objects.create(user=instance) 
        
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        username = instance.username
        if isinstance(username, unicode):
            username = username.encode('utf-8')
        p.activation_key = hashlib.sha1(salt+username).hexdigest()  #40 characters
        p.save()
        
post_save.connect(create_user_profile, sender=User)    

class Purchasable(m.Model): 
    price = m.DecimalField("$", max_digits=10, decimal_places=2, default = "0.00")    

    order = m.ForeignKey("Order",related_name="items",blank=True,null=True)

class Order(m.Model): 
    total_price = m.DecimalField("$", max_digits=10, decimal_places=2, default = "0.00")
    coupon = m.ForeignKey("Coupon",related_name="orders",null=True,blank=True)
    user_prof = m.ForeignKey("UserProfile",related_name="orders")

    def calc_total_price(self): 
        price  = float(self.items.aggregate(m.Sum('price'))['price__sum'])
        if self.coupon:
            price  -= self.coupon.discount(price)
        self.total_price = "%.2f"%price
        self.save()    


class Coupon(m.Model):     
    code = CouponCodeField("code",max_length=20)

    is_percent = m.BooleanField("%",default=False)   
    #is_giftcard = m.BooleanField("GiftCard",default=False)
    permanent = m.BooleanField("permanent",default=False)
    single_use_per_user = m.BooleanField("Once per user", default=False)
    user_prof = m.ForeignKey("UserProfile",related_name="coupons",blank=True,null=True)    

    discount_amount = m.DecimalField("$ discount",
                                     max_digits=10,
                                     decimal_places=2,
                                     default = "0.00")
    uses_left = m.IntegerField("# uses",default=1)
    expires = TodayOrLaterField(blank=True,default=None)

    def is_valid(self,user): 
        """check to see if the given user is allowed to use this coupon""" 
        if self.single_use_per_user: 
            try: 
                Order.objects.filter(coupon=self,user_prof=user.get_profile()).get()
                #it exits, so they have used it
                return False
            except Order.DoesNotExist as err: #then you're ok
                pass
        elif self.user_prof and user.get_profile()!=self.user_prof: 
            return False
        elif (not self.permanent) and self.uses_left < 1: #used up
            return False
        elif self.expires < datetime.date.today(): #expired
            return False

        return True

    def discount(self,price): 
        discount = float(self.discount_amount)
        if self.is_percent: #percentage discount
            return price*discount/100.0

        #dollar amount
        if discount >= price:
            return price #free, but not worth more than the price

        return discount


class Club(Purchasable):

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
    
    @property
    def sorted_seasons(self): 
        return self.seasons.order_by('year').reverse().all()

    def assign_dibs(self):
        """looks through the most recent events to assign 
        dibs to anyone who has earned it.""" 
        today = datetime.date.today()
        #find last N events
        recent_events = Event.objects.filter(season__club=self,
                                             sessions__isnull=False,
                                             sessions__results__isnull=False
                                             ).\
            order_by('-date')[:self.events_for_dibs].\
            annotate().all()
        if len(recent_events) != self.events_for_dibs: 
            #there have not been enough events yet to grant dibs
            return 

        #look for all dibs with drivers who have a registration in one of the last N events
        dibs = Dibs.objects.filter(user_profile__regs__event__in=recent_events,
                                   user_profile__regs__results__isnull=False).all()	
        for d in dibs: 
            time_held = d.expires-d.created
            months_held = time_held.days/30 #gets the whole number of months held, drops remainder
            if months_held > 12: 
                months_held = 12 #can't hold for more than 1 year
            d.duration = months_held*30
            d.expires = recent_events[0].date+datetime.timedelta(days=months_held*30)
            d.save()

        #check for new users who earned dibs
        #look for people who have used the same num/class in the last N events and don't already have dibs     

        regs = Registration.objects.values('number','race_class','user_profile').\
            filter(event__in=recent_events,
                   results__isnull=False,
                   race_class__allow_dibs=True).\
            annotate(reg_count=m.Count('number')).\
            filter(reg_count=self.events_for_dibs).all()

        try: 
            next_event = Event.objects.filter(season__club=self,date__gt=today).order_by('date')[0]
            #get dibs for one month past the date of the next event
            duration = 30
            expires =  next_event.date + datetime.timedelta(days=duration)
        except IndexError: 
            #if there is no future even in the system yet, just give it to you for 6 months
            duration = 180
            expires = today+datetime.timedelta(days=180)

        #get or create because someone with dibs might have run the last X events and be in this list
        for reg in regs: 
            up = UserProfile.objects.get(id=reg['user_profile'])
            dibs,created = Dibs.objects.get_or_create(number=reg['number'],
                                                      race_class_id=reg['race_class'],
                                                      club=self,
                                                      user_profile=up, 
                                                      defaults={'expires':expires,'duration':duration})



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

    def is_active_member(self,user): 

        try: 
            membership = Membership.objects.filter(user=user,
                                                   club=self,
                                                   valid_thru__gt=datetime.date.today()).get()
            return True
        except Membership.DoesNotExist: 
            return False


class Membership(Purchasable): 

    num = m.IntegerField("ID #",null=True,blank=True,default=None)

    start = m.DateField("Member Since")
    valid_thru = m.DateField("Valid Through")

    user = m.ForeignKey(User,related_name="memberships")
    club = m.ForeignKey("Club",related_name="memberships")

    _anon_f_name = m.CharField(max_length=50,blank=True,null=True,default=None)
    _anon_l_name = m.CharField(max_length=50,blank=True,null=True,default=None)

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
                ret = Membership.objects.filter(club=self.club).aggregate(m.Max('num'))
                num = ret['num__max']
                self.num = num+1
            except Membership.DoesNotExist: 
                self.num = 100

        super(Membership,self).save()


class RaceClass(m.Model): 
    name = m.CharField('Class Name',max_length=4)
    pax = m.FloatField('PAX multiplier')

    pax_class = m.BooleanField('PAX Class',default=False)
    description = m.TextField("Description",blank=True,default="")
    user_reg_limit = m.IntegerField("Limit for Users",null=True,default=None)
    event_reg_limit = m.IntegerField("Limit per Event",null=True,default=None)
    allow_dibs = m.BooleanField("dibs",default=True)
    hidden = m.BooleanField("hidden",default=False,
                            help_text="Hidden race classes can't be selected by users for registration."+\
                            "These race classes are used for index/bump-class results")

    club = m.ForeignKey('Club',related_name='race_classes')

    def __unicode__(self): 
        return u"%s %1.3f"%(self.name,self.pax)

class Dibs(m.Model): 
    created = m.DateField(auto_now_add=True)
    expires = m.DateField("Expires")
    duration = m.IntegerField("#of days",
                              help_text="# of days after the most recent event a User ran in the Dibs is valid for",
                              default=30)
    number = m.IntegerField("Number")    
    race_class = m.ForeignKey('RaceClass',related_name='+')
    club = m.ForeignKey("Club",related_name='dibs')
    user_profile = m.ForeignKey(UserProfile,related_name='dibs')

    def __unicode__(self):
        return "%d %s, for %s"%(self.number,self.race_class.name,self.user.username)


class Season(m.Model): 
    year = m.IntegerField(default=None)
    drop_lowest_events = m.IntegerField('# of Events to drop from points calculations',
                                        default=0)    

    club = m.ForeignKey('Club',related_name="seasons")
    
    def upcoming_events(self): 
        return self.events.exclude(date__lt=datetime.date.today()).order_by('date').all()
        #return self.events.all()

    def complete_events(self): 
        return self.events.exclude(date__gte=datetime.date.today()).order_by('-date')

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
    
    note = m.TextField('notes', blank=True)

    reg_close = m.DateTimeField('Registration Close Date',blank=True,null=True)

    member_price = m.DecimalField("Price for club members", max_digits=10,
                                  decimal_places=2, default="0.00")
    non_member_price = m.DecimalField("Price for non club Members", max_digits=10, 
                                      decimal_places=2, default="0.00")
    non_pre_pay_penalty = m.DecimalField("Extra Cost if paying at the event", max_digits=10, 
                                         decimal_places=2, default="0.00")

    reg_limit = m.IntegerField("Reg. Limit", default=0, help_text="Maximum number of registrations allowed. ")

    count_points = m.BooleanField("Include this event in season point totals",default=True)
    multiplier = m.IntegerField("Multiplier on the total number of points an event is worth",default=1)

    season = m.ForeignKey('Season',related_name="events")    

    #TODO: modify on_delete to set to club default location
    location = m.ForeignKey('Location',blank=True,null=True,on_delete=m.SET_NULL)

    #This is to allow for registration of one event to automaticaly count toward any child events as well
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

    def calc_results(self): 
        #all regs that are valid, from this event

        #find all results from any pax classes
        regs = Registration.objects.filter(event=self).annotate(n_results=m.Count('results')).\
            filter(n_results=len(self.sessions.all())).all()
        #calc all penalty times, index times, 
        for reg in regs: 
            reg.calc_times()

        #find all the regs, now ordered by time
        regs = Registration.objects.annotate(n_results=m.Count('results')).filter(
            event=self,n_results=len(self.sessions.all())).order_by('total_index_time').all()

        #assign index points, sort results into classes, then assign class points
        race_classes = dict()

        for i,reg in enumerate(regs): 
            if i == 0 : #fastest index time!
                index_ftd = reg

            #these get on the list sorted, because the whole list is sorted
            if reg.bump_class: 
                key = reg.bump_class
            else: 
                key = reg.race_class
            race_classes.setdefault(key,[]).append(reg) 
            #assign class points, based on position in the list

            place = len(race_classes[key])
            first_place_time = race_classes[key][0].total_index_time
            reg.class_points = class_points(place,first_place_time,reg.total_index_time)

            #place is i+1
            reg.index_points = index_points(i+1,index_ftd.total_index_time,reg.total_index_time)
            reg.save()

        return race_classes

    def get_results(self):
        #check if valid points calculations, if not calc_results
        regs = Registration.objects.annotate(n_results=m.Count('results')).filter(
            event=self,n_results=len(self.sessions.all())).order_by('total_index_time').\
            all()

        return regs

    def get_class_results(self,race_class): 
        """Returns a list of lists of all registrations which qualified for points and were in 
        a class."""
        regs = Registration.objects.filter(event=self,
                                           race_class=race_class).\
            annotate(result_count=m.Count('results')).\
            filter(result_count=m.F('n_event__sessions')).\
            select_related('results').all()

        for reg in regs: 
            reg.calc_times()


        regs.sort(key=lambda reg: reg.total_index_time)
        return regs

    def clean(self): 
        if self.reg_close.date() >= self.date: 
            raise ValidationError("Registration must close before the date of the event.")

    def __unicode__(self): 
        return self.safe_name

class Registration(Purchasable):
    car = m.ForeignKey("Car",related_name="regs",blank=True,null=True,on_delete=m.SET_NULL)
    number = m.IntegerField("Car Number")
    race_class = m.ForeignKey("RaceClass",related_name="+")
    pax_class  = m.ForeignKey("RaceClass",related_name="+",blank=True,null=True)
    bump_class = m.ForeignKey("RaceClass",related_name="+",blank=True,null=True)
    run_heat = m.IntegerField("Run Heat",blank=True,null=True,default=None)
    work_heat = m.IntegerField("Work Heat",blank=True,null=True,default=None)
    checked_in = m.BooleanField("Checked In",default=False)


    total_raw_time = m.FloatField('Total Raw Time', blank=True, null=True, default = None)
    total_index_time = m.FloatField('Total Index Time', blank=True, null=True, default = None)

    class_points = m.IntegerField(blank=True,null=True)
    index_points = m.IntegerField(blank=True,null=True)

    event = m.ForeignKey("Event",related_name="regs")

    #reg_detail = m.ForeignKey("RegDetail",related_name="regs",blank=True,null=True)
    user_profile = m.ForeignKey('UserProfile',related_name="regs",blank=True,null=True)

    @property
    def user(self):
        return self.user_profile.user

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
        if self.user_profile: 
            return self.user_profile.user.first_name
        elif self._anon_f_name: 
            return self._anon_f_name
        return "Driver"

    @property
    def last_name(self):
        if self.user_profile: 
            return self.user_profile.user.last_name
        elif self._anon_l_name: 
            return self._anon_l_name
        return "Not On File" 

    def __unicode__(self):
        if self.user_profile: 
            return "%s for %s"%(self.user_profile.user.username,self.event.name)
        return "anon: %s %s for %s"%(self.first_name,self.last_name,self.event.name)


    def calc_times(self): 
        """Finds the lowest time for each associated result, adds them together, then 
        calculates a new combined index time based on the associated race_class or 
        pax_class"""

        self.total_raw_time = sum([res.best_run.calc_time for res in self.results.all() if res.best_run])
        if self.pax_class:
            pax = self.pax_class.pax
        else: 
            pax = self.race_class.pax
        self.total_index_time = self.total_raw_time*pax
        self.save()


    def associate_with_user(self,user): 
        self._anon_f_name = "N/A"
        self._anon_l_name = "N/A"
        self.user_profile = UserProfile.objects.get(user__username=user)

    def make_assoc_regs(self): 
        """creates regs for all child events of the event this registration is associated with""" 
        try: 
            events = self.event.child_events.exclude(regs__user_profile=self.user_profile,
                                                           regs__user_profile__isnull=False).all()

            #only grab child events which don't already have an associated reg
            for event in events: 
                reg = Registration()
                reg.number = self.number
                reg.race_class = self.race_class
                reg.pax_class = self.pax_class
                reg.user_profile = self.user_profile
                reg.event = event
                reg.save()
        except Event.DoesNotExist: 
            return 

    def update_assoc_regs(self): 

        other_regs = Registration.objects.filter(user_profile=self.user_profile)
        for reg in other_regs: 
            reg.number = self.number
            reg.race_class = self.race_class
            reg.pax_class = self.pax_class
            reg.save()


    def clean(self): 
        if not self.event.allow_number_race_class(self.number,self.race_class):
            raise ValidationError('%d %s is already taken, pick another number.'%(self.number,self.race_class.name))

        #if necessary, check to make sure user has not already run the max times in this class
        if self.user_profile and self.race_class.user_reg_limit:	
            reg_count = Registration.objects.filter(event__season__club=self.event.season.club,
                                                    user_profile__user=self.user_profile.user,
                                                    user_profile__isnull=False,
                                                    race_class=self.race_class).count()
            if reg_count >= self.race_class.user_reg_limit:
                raise ValidationError("You have reached the registration limit for %s."%self.race_class.name)

        if self.race_class.event_reg_limit: 
            reg_count = Registration.objects.filter(event=self.event,race_class=self.race_class).count()
            if reg_count >= self.race_class.event_reg_limit: 
                raise ValidationError("Only %d registrations for %s are allowed "
                                      "for an event. The class is full"%(self.race_class.event_reg_limit,
                                                                         self.race_class.name))

        if self.event.reg_limit: 
            reg_count = Registration.objects.filter(event=self.event).count()
            if reg_count >= self.event.reg_limit: 
                raise ValidationError('Only %d registrations are allowed for the event. The event is full'%self.event.reg_limit)


class Session(m.Model): 
    name = m.CharField(max_length=30)
    event = m.ForeignKey("Event",related_name="sessions")
    course = m.OneToOneField("Course",blank=True,null=True)

    def __unicode__(self): 
        return self.name

class Result(m.Model): 
    best_run = m.OneToOneField("Run",related_name="+",null=True)
    reg = m.ForeignKey("Registration",related_name="results")

    session = m.ForeignKey("Session",related_name="results") 

    def __unicode__(self): 
        return unicode(self.best_run)

    def find_best_run(self): 
        #find the best run        
        try:         
            br =  Run.objects.filter(result=self,
                                     result__runs__penalty__isnull=True).\
                order_by('calc_time')[0]
            self.best_run = br
            self.save()
            return br
        except IndexError: 
            return None


class Run(m.Model):     
    base_time = m.FloatField('Base Time')
    calc_time = m.FloatField('Calculated Time')
    index_time = m.FloatField('Indexed Time')

    cones = m.IntegerField(default=0)
    penalty = m.CharField(default=None,max_length=10,null=True)

    result = m.ForeignKey("Result",related_name="runs")

    def _set_times(self): 
        self.calc_time = self.base_time+2.0*self.cones
        self.index_time = self.calc_time*self.result.reg.race_class.pax   
        return (self.calc_time,self.index_time)

    def save(self): 
        self._set_times()
        super(Run,self).save()
        self.result.find_best_run()


    def __unicode__(self): 
        if self.penalty: 
            return self.penalty
        if self.cones: 
            return u"3.3f, +%d cones (3.3f)"%(self.calc_time,self.cones,self.index_time)

        return u"%3.3f(%3.3f)"%(self.calc_time,self.index_time)

class Location(m.Model):

    name = m.CharField('Location Name',max_length=100)

    address = m.CharField('Address',max_length=250)

    club = m.ForeignKey('Club',related_name='locations')

    def __unicode__(self): 
        return self.name

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

    user_profile = m.ForeignKey(UserProfile,related_name="cars")
    
    @property
    def user(self): 
        return self.user_profile.user
    
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

