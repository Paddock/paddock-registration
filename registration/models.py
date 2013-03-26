import os
import datetime
from urllib import pathname2url
import re
import hashlib
import random

from django.db import models as m
#from django.contrib.localflavor.us.forms import USStateField, USZipCodeField
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.files.storage import FileSystemStorage


from django.template.loader import render_to_string

from django.contrib.auth.models import User, Group, Permission
from django.db.models.signals import post_save, post_delete

from django.utils.timezone import now as django_now

from django.conf import settings 

#TODO: need to replace this with some sort of plugin system
from registration.points_calculators.nora_class_points import calc_points as calc_class_points
from registration.points_calculators.nora_index_points import calc_points as calc_index_points


def urlsafe(name): 
    safe = re.sub(r'[\s\W]', '', name)
    safe = pathname2url(safe)
    safe = safe.lower()    

    return safe


def find_user(query):
    """look for a driver that might match any of these attrs"""

    return User.objects.filter(m.Q(last_name__icontains=query) |
                               m.Q(first_name__icontains=query) |
                               m.Q(username__icontains=query)).all()


def clean_dibs(): 
    for c in Club.objects.all(): 
        c.assign_dibs()

    Dibs.objects.filter(expires__lt=datetime.date.today()).delete()	


class TodayOrLaterField(m.DateField): 
    def validate(self, value, model_instance): 
        super(TodayOrLaterField, self).validate(value, model_instance)

        if value and value < datetime.date.today()+datetime.timedelta(days=1):
            raise ValidationError("Date must be at least one day from now")


class CouponCodeField(m.CharField): 
    def validate(self, value, model_instance): 
        super(CouponCodeField, self).validate(value, model_instance)

        if " " in value: 
            raise ValidationError("Spaces not allowed in the code")


class OverwriteStorage(FileSystemStorage):
    def _save(self, name, content):
        if self.exists(name):
            self.delete(name)
        return super(OverwriteStorage, self)._save(name, content)

    def get_available_name(self, name):
        return name            


class UserProfile(m.Model): 
    
    user = m.OneToOneField(User)
    
    activation_key = m.CharField('activation key', max_length=40)
        
    address = m.CharField('Home Address', max_length=150, null=True, blank=True)
    city = m.CharField('City', max_length=25, null=True, blank=True)
    state = m.CharField('State', max_length=25, null=True, blank=True)
    zip_code = m.CharField('Zip Code', max_length=13, null=True, blank=True) 

    class Meta: 
        permissions = (("view_user", "Can see information about users"),)
    
    def __unicode__(self):
        return u'Profile %s'%self.pk
    
    def send_activation_email(self): 

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        username = self.user.username
        if isinstance(username, unicode):
            username = username.encode('utf-8')
        #40 characters
        self.activation_key = hashlib.sha1(salt+username).hexdigest() 
        self.save() 
        
        ctx_dict = {'activation_key': self.activation_key,
                    'SITE_URL': settings.SITE_URL,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'user': self.user}
        subject = render_to_string('registration/activation_email_subject.txt',
                                   ctx_dict)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string('registration/activation_email.txt',
                                   ctx_dict)
        print self.user.email
        self.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)        

    def get_next_events(self): 
        #today = datetime.datetime.today()
        #TODO: get all events that user is registered for, 
        #      or that are coming up for clubs that you're member of  
        ret = None
        for m in self.memberships.all(): 
            e = m.club.upcoming_events()
            if e != None:
                if ret!=None: 
                    ret | e
                else: 
                    ret = e   
        if ret != None: 
            return ret.order_by('date')   
        return False     

    def is_member(self, club): 
        today = datetime.date.today()
        for m in self.memberships.all(): 
            if m.club == club and m.paid and m.valid_thru >= today: 
                return m
        return False    

    def is_registered(self, event): 
        for r in self.registrations.all():
            if r.event == event: 
                return r
        return False


#causes creation of user profile just after new users are created    
def create_user_profile(sender, instance, created, **kwargs): 
    if created:
        p = UserProfile.objects.create(user=instance) 
        p.save()
        
post_save.connect(create_user_profile, sender=User)    


class Purchasable(m.Model): 
    price = m.DecimalField("$", max_digits=10, decimal_places=2, default="0.00")    
    order = m.ForeignKey("Order", related_name="items", blank=True, null=True)
    paid = m.BooleanField('paid', default=False)


class Order(m.Model): 
    total_price = m.DecimalField("$", max_digits=10, decimal_places=2, default="0.00")
    coupon = m.ForeignKey("Coupon", related_name="orders", null=True, blank=True)
    user_prof = m.ForeignKey("UserProfile", related_name="orders")

    def calc_total_price(self): 
        price = float(self.items.aggregate(m.Sum('price'))['price__sum'])
        if self.coupon:
            price -= self.coupon.discount(price)
        self.total_price = "%.2f"%price
        self.save()    


class Coupon(m.Model):     
    code = CouponCodeField("code", max_length=20)

    is_percent = m.BooleanField("%", default=False)   
    #is_giftcard = m.BooleanField("GiftCard",default=False)
    permanent = m.BooleanField("permanent", default=False)
    single_use_per_user = m.BooleanField("Once per user", default=False)
    user_prof = m.ForeignKey("UserProfile", related_name="coupons", blank=True, null=True)  
    club = m.ForeignKey("Club", related_name="coupons")  

    discount_amount = m.DecimalField("$ discount",
                                     max_digits=10,
                                     decimal_places=2,
                                     default="0.00")
    uses_left = m.IntegerField("# uses", default=1)
    expires = TodayOrLaterField(null=True, blank=True, default=None)

    def is_valid(self, user): 
        """check to see if the given user is allowed to use this coupon""" 
        if self.single_use_per_user: 
            try: 
                Order.objects.filter(coupon=self, user_prof=user.get_profile()).get()
                #it exits, so they have used it
                return False
            except Order.DoesNotExist: #then you're ok
                pass
        elif self.user_prof and user.get_profile()!=self.user_prof: 
            return False
        elif (not self.permanent) and self.uses_left < 1: #used up
            return False
        elif self.expires < datetime.date.today(): #expired
            return False

        return True

    def discount(self, price): 
        discount = float(self.discount_amount)
        if self.is_percent: #percentage discount
            return price*discount/100.0

        #dollar amount
        if discount >= price:
            return price #free, but not worth more than the price

        return discount


class Club(Purchasable):

    name = m.CharField('Club Name', max_length=100)
    safe_name = m.CharField("safe_name", max_length=100, primary_key=True, unique=True) 

    #created = m.DateTimeField(auto_now_add=True)
    #last_mod = m.DateTimeField(auto_now=True)

    new_member_cost = m.DecimalField('New Membership Price', 
                                     max_digits=10,
                                     decimal_places=2,
                                     default="0.00") 
    renew_cost = m.DecimalField('Membership Renewal Price', 
                                max_digits=10,
                                decimal_places=2, default="0.00") 
    membership_terms = m.TextField('Membership Terms', blank=True)

    process_payments = m.BooleanField('Process Payments', default=True)
    paypal_email = m.CharField('Paypal Email Address', max_length=100, blank=True,
                               validators=[validate_email])

    address = m.CharField('Mailing Address', max_length=100, blank=True, null=True)
    city = m.CharField('City', max_length=100, blank=True, null=True)
    state = m.CharField('State', max_length=25, blank=True, null=True) #USStateField('State')
    zip_code = m.CharField('Zip Code', max_length=12, blank=True, null=True) #USZipCodeField('Zip Code')

    events_for_dibs = m.IntegerField("# of events to get dibs", default=3)

    default_location = m.OneToOneField("Location", related_name="+", blank=True, null=True)

    group = m.OneToOneField(Group, related_name="club", blank=True, null=True)

    def __unicode__(self): 
        return self.safe_name

    def full_clean(self, *args, **kwargs):
        self.safe_name = urlsafe(self.name)
        super(Club, self).full_clean(*args, **kwargs) 

    def save(self, *args, **kwargs):
        self.safe_name = urlsafe(self.name)
        super(Club, self).save(*args, **kwargs)       
    
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

        regs = Registration.objects.values('number', 'race_class', 'user_profile').\
            filter(event__in=recent_events,
                   results__isnull=False,
                   race_class__allow_dibs=True).\
            annotate(reg_count=m.Count('number')).\
            filter(reg_count=self.events_for_dibs).all()

        try: 
            next_event = Event.objects.filter(season__club=self, date__gt=today).order_by('date')[0]
            #get dibs for one month past the date of the next event
            duration = 30
            expires = next_event.date + datetime.timedelta(days=duration)
        except IndexError: 
            #if there is no future even in the system yet, just give it to you for 6 months
            duration = 180
            expires = today+datetime.timedelta(days=180)

        #get or create because someone with dibs might have run the last X events and be in this list
        for reg in regs: 
            up = UserProfile.objects.get(id=reg['user_profile'])
            dibs, created = Dibs.objects.get_or_create(number=reg['number'],
                                                      race_class_id=reg['race_class'],
                                                      club=self,
                                                      user_profile=up, 
                                                      defaults={'expires': expires, 'duration': duration})

    def check_dibs(self, number, race_class): 
        """Checks to see if anyone has dibs on the given number/race_class for a club.
        returns True if someone has dibs on the number/race_class
        """

        try: 
            if isinstance(race_class, str): 
                Dibs.objects.filter(club=self, number=number, race_class__name=race_class).get()
            else: 	
                Dibs.objects.filter(club=self, race_class=race_class, number=number).get()
        except Dibs.DoesNotExist: 
            return False
        return True     

    def is_active_member(self, user): 

        try: 
            Membership.objects.filter(user_prof=user.get_profile(),
                club=self, valid_thru__gt=datetime.date.today()).get()
            return True
        except Membership.DoesNotExist: 
            return False

    def upcoming_events(self):
        season = self.seasons.all()[0]
        if season:
            return season.upcoming_events()
        return None  


def remove_club(sender,instance,signal,using,**kwargs): 

    Permission.objects.get(codename="%s_admin"%instance.safe_name).delete()
    Group.objects.get(name="%s_admin"%instance.safe_name).delete()
post_delete.connect(remove_club, sender=Club)

#causes creation of club admin permissions after club is saved  
def create_club(sender, instance, created, **kwargs): 
    if created:
        club_content_type = ContentType.objects.get(app_label='registration', model='club')

        p = Permission.objects.create(codename="%s_admin"%instance.safe_name,
                                       name="%s Administrator"%instance.name,
                                       content_type=club_content_type)
        p.save()

        user_p = Permission.objects.get(codename="view_user")

        g = Group()
        g.name = "%s_admin"%instance.safe_name
        g.save()

        g.permissions.add(p)
        g.permissions.add(user_p)

        instance.group = g
        instance.save()
        
post_save.connect(create_club, sender=Club)               


class Membership(Purchasable): 

    num = m.IntegerField("ID #", null=True, blank=True, default=None)

    start = m.DateField("Member Since")
    valid_thru = m.DateField("Valid Through")

    user_prof = m.ForeignKey('UserProfile', related_name="memberships")
    club = m.ForeignKey("Club", related_name="memberships")

    _anon_f_name = m.CharField(max_length=50, blank=True, null=True, default=None)
    _anon_l_name = m.CharField(max_length=50, blank=True, null=True, default=None)

    def __unicode__(self):
        return "%s in %s>"%(self.user.username, self.club.safe_name)

    @property    
    def f_name(self):
        if self.user_prof: 
            return self.user_prof.user.first_name
        return self._anon_f_name

    @property 
    def l_name(self): 
        if self.user_prof: 
            return self.user_prof.user.last_name
        return self._anon_l_name   

    def clean(self): 
        try: 
            Membership.objects.filter(club=self.club, num=self.num).get()
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

        super(Membership, self).save()


class RaceClass(m.Model): 
    name = m.CharField('Class Name', max_length=20)
    abrv = m.CharField('Arbeviation', max_length=4)
    pax = m.FloatField('PAX multiplier',default=1.0)

    pax_class = m.BooleanField('PAX Class', default=False)
    default_pax_class = m.ForeignKey('self', null=True, blank=True)
    bump_class = m.BooleanField('Bump Class', default=False)
    hidden = m.BooleanField("hidden", default=False,
                            help_text="Hidden race classes can't be selected by users for registration."+\
                            "These race classes are used for index/bump-class results and non-pickable pax classes")
    
    description = m.TextField("Description", blank=True, default="")
    user_reg_limit = m.IntegerField("Limit for Users", null=True, default=None)
    event_reg_limit = m.IntegerField("Limit per Event", null=True, default=None)
    allow_dibs = m.BooleanField("dibs", default=True)
    
    club = m.ForeignKey('Club', related_name='race_classes')

    def __unicode__(self): 
        return u"Class: %s, index: %1.3f"%(self.abrv, self.pax)
    
    def __cmp__(self, other): 
        if other: 
            return cmp(self.name, other.name)
        else: 
            return 1


class Dibs(m.Model): 
    created = m.DateField(auto_now_add=True)
    expires = m.DateField("Expires")
    duration = m.IntegerField("#of days",
                              help_text="# of days after the most recent event a User ran in the Dibs is valid for",
                              default=30)
    number = m.IntegerField("Number")    
    race_class = m.ForeignKey('RaceClass', related_name='+')
    club = m.ForeignKey("Club", related_name='dibs')
    user_profile = m.ForeignKey(UserProfile, related_name='dibs')

    def __unicode__(self):
        return "%d %s, for %s"%(self.number, self.race_class.name, self.user.username)


class Season(m.Model): 

    class Meta: 
        ordering = ['-year']

    year = m.IntegerField(default=None)
    drop_lowest_events = m.IntegerField('# of Events to drop from points calculations',
                                        default=0)    

    club = m.ForeignKey('Club', related_name="seasons")
    
    def upcoming_events(self): 
        return self.events.exclude(date__lt=datetime.date.today()).order_by('date').all()
        #return self.events.all()

    def complete_events(self): 
        return self.events.exclude(date__gte=datetime.date.today()).order_by('-date')
    
    def points_as_of(self, date=None): 
        """gets a lists of index_points,[(user,{'n_regs':<int>,'points':<int>,'appe':<int>}),...], and 
        class_points, [(race_class,[user{'n_regs':<int>,'points':<int>,'appe':<int>},...])], as of the given date"""
        
        event_count = self.events.filter(season=self, count_points=True).count()
        if event_count > self.drop_lowest_events: 
            limit = event_count - self.drop_lowest_events
        else: 
            limit = event_count
         
        q = Registration.objects.select_related('user_profile', 'pax_class', 'race_class'
                                                 'event__season', 'results')
        if date: 
            regs = q.filter(event__season=self, event__count_points=True,
                            results__isnull=False, user_profile__isnull=False,
                            event__date__lte=date).\
                distinct().order_by('-index_points').all()
        else: 
            regs = q.filter(event__season=self, event__count_points=True,
                            results__isnull=False, user_profile__isnull=False).\
                distinct().order_by('-index_points').all()
        
        index_sets = dict()
        class_sets = dict()
        
        for reg in regs: 
            up = reg.user_profile
            class_key = reg.race_class
            if reg.pax_class: 
                class_key = reg.pax_class
            
            index_sets.setdefault(up, {'n_regs': 0, 'points': 0, 'appe': 0}) 
            class_sets.setdefault(class_key, dict())
            
            if index_sets[up]['n_regs'] < limit: 
                index_sets[up]['n_regs'] += 1
                index_sets[up]['points'] += reg.index_points
                index_sets[up]['appe'] = int(round(index_sets[up]['points']/float(index_sets[up]['n_regs']), 0))
                
                class_sets[class_key].setdefault(up, {'n_regs': 0, 'points': 0, 'appe': 0})
                class_sets[class_key][up]['n_regs']+=1
                class_sets[class_key][up]['points']+=reg.class_points
                class_sets[class_key][up]['appe'] = int(round(class_sets[class_key][up]['points']/float(class_sets[class_key][up]['n_regs'])))
                
        index_points = sorted(index_sets.items(), key=lambda t: t[1]['points'], reverse=True) 
        class_points = sorted(class_sets.items(), key=lambda t: t[0].abrv) 
        for i, reg_set in enumerate(class_points):  
            class_points[i] = (reg_set[0], sorted(reg_set[1].items(), 
                                                 key=lambda t: t[1]['points'], reverse=True))
           
        return index_points, class_points 
    
    def __unicode__(self): 
        return u"%d"%self.year


class Event(m.Model): 

    class Meta: 
        ordering = ['date']

    name = m.CharField('Name', max_length=100)
    safe_name = m.CharField(max_length=100)

    date = m.DateField('Event Date')
    
    note = m.TextField('notes', blank=True, null=True)

    reg_close = m.DateTimeField('Registration Close Date', blank=True, null=True)

    member_price = m.DecimalField("Price for club members", max_digits=10,
                                  decimal_places=2, default="0.00")
    non_member_price = m.DecimalField("Price for non club Members", max_digits=10, 
                                      decimal_places=2, default="0.00")
    non_pre_pay_penalty = m.DecimalField("Extra Cost if paying at the event", max_digits=10, 
                                         decimal_places=2, default="0.00")

    reg_limit = m.IntegerField("Reg. Limit", default=0, help_text="Maximum number of registrations allowed. ")

    count_points = m.BooleanField("Include this event in season point totals", default=True)
    multiplier = m.IntegerField("Multiplier on the total number of points an event is worth", default=1)

    season = m.ForeignKey('Season', related_name="events") 
    club = m.ForeignKey('Club', related_name="+")   

    #TODO: modify on_delete to set to club default location
    location = m.ForeignKey('Location', blank=True, null=True, on_delete=m.SET_NULL)

    #This is to allow for registration of one event to automaticaly count toward any child events as well
    child_events = m.ManyToManyField("self", symmetrical=False, related_name="parent_events",
                                     blank=True, null=True,
                                     help_text="When drivers register for this event, they will automatically be" 
                                     "registered for all the associated events listed here.")
    
    @property
    def reg_is_open(self): 
        return django_now() < self.reg_close
    
    def is_regd(self, user): 
        try: 
            reg = self.regs.filter(user_profile=user.get_profile()).get()
            return reg
        except Registration.DoesNotExist: 
            return False

    #do this in clean and save because sometimes clean is not called??
    def full_clean(self, *args, **kwargs): 
        self.safe_name = urlsafe(self.name)
        super(Event, self).full_clean(*args, **kwargs)

    def save(self, *args, **kwargs): 
        self.safe_name = urlsafe(self.name)
        super(Event, self).save(*args, **kwargs)        

    def allow_number_race_class(self, reg): 
        """Checks to see if the specified registration has a unique number and 
        race_class for the event"""

        regs = self.regs.filter(number=reg.number,	                     
                                race_class=reg.race_class)

        reg_check = regs.count()

        #Check if the number/class is used in any child events
        child_regs = self.child_events.all().\
            filter(regs__number=reg.number, regs__race_class=reg.race_class)

        child_reg_check = child_regs.count()

        #existing reg, trying to change to a taken number
        if reg.pk and (reg_check and reg.pk!=regs[0].pk or (child_reg_check and reg.pk!=child_regs[0].pk)): #someone else already has this
            return False 
        
        if reg.pk and reg_check==1 and child_reg_check <=1: #then it exists, so you need to make sure it's still unique
            return True
            
        #it does not exists, so check if the number/class is used in this event 
        #make sure no one has dibs on that
        elif reg_check == 0 and child_reg_check == 0 and not self.season.club.check_dibs(reg.number, reg.race_class): 
            return True

        return False	

    def calc_results(self): 
        #all regs that are valid, from this event

        #find all results from any pax classes
        regs = Registration.objects.filter(event=self).annotate(n_results=m.Count('results')).\
            filter(n_results=self.sessions.all().count()).all()
        #calc all penalty times, index times, 
        for reg in regs: 
            reg.calc_times()
            print "TESTING:", reg.first_name, reg.last_name, reg.total_index_time, 
            print "    ", reg.results.all()


        #find all the regs, now ordered by time
        regs = Registration.objects.annotate(n_results=m.Count('results')).filter(
            event=self, n_results=self.sessions.all().count()).order_by('total_index_time').all()

        #assign index points, sort results into classes, then assign class points
        race_classes = dict()

        for i, reg in enumerate(regs): 
            if i == 0: #fastest index time!
                index_ftd = reg

            #these get on the list sorted, because the whole list is sorted
            if reg.bump_class: 
                key = reg.bump_class
            elif reg.pax_class: 
                key = reg.pax_class
            else: 
                key = reg.race_class
            race_classes.setdefault(key, []).append(reg) 
            #assign class points, based on position in the list

            place = len(race_classes[key])
            first_place_time = race_classes[key][0].total_index_time
            reg.class_points = calc_class_points(place, first_place_time, reg.total_index_time)

            #place is i+1
            reg.index_points = calc_index_points(i+1, index_ftd.total_index_time, reg.total_index_time)
            reg.save()

        return race_classes

    def get_results(self):
        
        n_sessions = self.sessions.all().count()
        #check if valid points calculations, if not calc_results        
        
        regs = Registration.objects.annotate(n_results=m.Count('results'),
                                             n_runs=m.Count('results__best_run'))\
            .filter(event=self, n_results=n_sessions).\
            order_by('-n_runs', 'total_index_time').\
            all()

        return regs 

    def clean(self): 
        if self.reg_close.date() >= self.date: 
            raise ValidationError("Registration must close before the date of the event.")

    def __unicode__(self): 
        return self.safe_name


class Registration(Purchasable):
    car = m.ForeignKey("Car", related_name="regs", blank=True, null=True, on_delete=m.SET_NULL)
    number = m.IntegerField("Number")
    race_class = m.ForeignKey("RaceClass", limit_choices_to={'pax_class': False},
                              related_name="+")
    pax_class = m.ForeignKey("RaceClass", limit_choices_to={'pax_class': True},
                             verbose_name="Registration Type",
                             related_name="+", blank=True, null=True,
                             help_text="If you're not sure, run in Open Class")
    bump_class = m.ForeignKey("RaceClass", related_name="+", blank=True, null=True)
    run_heat = m.IntegerField("Run Heat", blank=True, null=True, default=None)
    work_heat = m.IntegerField("Work Heat", blank=True, null=True, default=None)
    checked_in = m.BooleanField("Checked In", default=False, editable=False)

    total_raw_time = m.FloatField('Total Raw Time', blank=True, null=True, default=None)
    total_index_time = m.FloatField('Total Index Time', blank=True, null=True, default=None)

    class_points = m.IntegerField(blank=True, null=True, editable=False)
    index_points = m.IntegerField(blank=True, null=True, editable=False)

    event = m.ForeignKey("Event", related_name="regs")
    club = m.ForeignKey("Club", related_name="+")

    user_profile = m.ForeignKey('UserProfile', related_name="regs", blank=True, null=True)
    
    #used only for anonymous regs
    _anon_f_name = m.CharField(max_length=50, default="N/A", editable=False)
    _anon_l_name = m.CharField(max_length=50, default="N/A", editable=False)
    _anon_car = m.CharField(max_length=50, default="N/A", editable=False)    
    
    @property
    def user(self):
        if self.user_profile is not None: 
            return self.user_profile.user
        else: 
            return AnonymousUser()

    @property
    def car_name(self): 
        if not self.car is None: 
            return "%d %s %s"%(self.car.year, self.car.make, self.car.model)
        elif self._anon_car:
            return self._anon_car
        return "N/A"

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
            return "%s for %s"%(self.user_profile.user.username, self.event.name)
        return "anon: %s %s for %s"%(self.first_name, self.last_name, self.event.name)

    def calc_times(self): 
        """Finds the lowest time for each associated result, adds them together, then 
        calculates a new combined index time based on the associated race_class or 
        pax_class"""
        runs = [res.find_best_run() for res in self.results.all().iterator()]
        
        self.total_raw_time = sum([r.calc_time for r in runs if r])
        if self.pax_class:
            pax = self.pax_class.pax*self.race_class.pax
        else: 
            pax = self.race_class.pax
        self.total_index_time = self.total_raw_time*pax
        self.save()

    def associate_with_user(self, user): 
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
                reg.club = self.club
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
        
        if not self.event.allow_number_race_class(self):
            raise ValidationError('%d %s is already taken, pick another number.'%(self.number, self.race_class.name))
        #if necessary, check to make sure user has not already run the max times in this class
        if self.user_profile and self.race_class.user_reg_limit:	
            reg_count = Registration.objects.filter(event__season__club=self.event.season.club,
                                                    user_profile__user=self.user_profile.user,
                                                    user_profile__isnull=False,
                                                    race_class=self.race_class).count()
            if reg_count >= self.race_class.user_reg_limit:
                raise ValidationError("You have reached the registration limit for %s."%self.race_class.name)

        if self.race_class.event_reg_limit: 
            reg_count = Registration.objects.filter(event=self.event, race_class=self.race_class).count()
            if reg_count >= self.race_class.event_reg_limit: 
                raise ValidationError("Only %d registrations for %s are allowed "
                                      "for an event. The class is full"%(self.race_class.event_reg_limit,
                                                                         self.race_class.name))

        if self.event.reg_limit: 
            reg_count = Registration.objects.filter(event=self.event).count()
            if reg_count >= self.event.reg_limit: 
                raise ValidationError('Only %d registrations are allowed for the event. The event is full'%self.event.reg_limit)

        check_regs = self.event.regs.select_related('race_class').\
                    filter(user_profile=self.user_profile,
                           user_profile__isnull=False).\
                    exclude(pk=self.pk)
        
        if check_regs.count(): 
            reg = check_regs[0]
            raise ValidationError('You have already registered to run as %d %s'%(reg.number, reg.race_class.abrv))

    def save(self): 
        self.full_clean()
        super(Registration, self).save()        


class Session(m.Model): 
    name = m.CharField(max_length=30)
    event = m.ForeignKey("Event", related_name="sessions")
    course = m.OneToOneField("Course", blank=True, null=True)
    club = m.ForeignKey("Club", related_name="+")

    def __unicode__(self): 
        return self.name


class Result(m.Model): 
    best_run = m.OneToOneField("Run", related_name="+", null=True)
    reg = m.ForeignKey("Registration", related_name="results")

    session = m.ForeignKey("Session", related_name="results") 
    club = m.ForeignKey("Club", related_name="+")

    def __unicode__(self): 
        return "Result id: %d"%self.pk

    def find_best_run(self): 
        #find the best run        
        try:     
            br = Run.objects.filter(result=self,
                  penalty__isnull=True).\
                  order_by('calc_time', 'base_time')[0]
            self.best_run = br
            self.save()
            return br
        except IndexError: 
            return 


class Run(m.Model):     
    base_time = m.FloatField('Base Time',default=0.0)
    calc_time = m.FloatField('Calculated Time', default=0.0)

    cones = m.IntegerField(default=0)
    penalty = m.CharField(default=None, max_length=10, blank=True, null=True)

    result = m.ForeignKey("Result", related_name="runs")
    club = m.ForeignKey("Club", related_name="+")

    def _set_times(self):
        self.calc_time = self.base_time+2.0*self.cones
        return self.calc_time

    def save(self): 
        self._set_times()
        super(Run, self).save()
        self.result.find_best_run()

    def __unicode__(self): 
        if self.penalty: 
            return self.penalty
        if self.cones: 
            if self.cones > 1: 
                return u"%3.3f +%d cones"%(self.calc_time, self.cones)
            return u"%3.3f +%d cone"%(self.calc_time, self.cones)
        
        return u"%3.3f"%(self.calc_time)


class Location(m.Model):

    name = m.CharField('Location Name', max_length=100)

    address = m.CharField('Address', max_length=250)

    club = m.ForeignKey('Club', related_name='locations')

    def __unicode__(self): 
        return self.name


def upload_course_to(course, file_name): 
    return os.path.join(course.event.club.safe_name, course.event.safe_name, "")    


class Course(m.Model): 
    name = m.CharField('Name', max_length=50)
    safe_name = m.CharField(max_length=50)

    img_loc = m.ImageField('Course Drawing', upload_to=upload_course_to)

    event = m.ForeignKey('Event', related_name="courses")
    club = m.ForeignKey("Club", related_name="+")

    def __unicode__(self): 
        return self.safe_name


class Car(m.Model): 
    name = m.CharField('Nickname', max_length=30, blank=True, null=True)
    color = m.CharField('Color', max_length=40, blank=True, null=True)
    year = m.IntegerField('Year', blank=True, null=True)    
    make = m.CharField('Make', max_length=40, blank=True, null=True)
    model = m.CharField('Model', max_length=40, blank=True, null=True)

    provisional = m.BooleanField('provisional', default=True)

    avatar = m.ImageField('Picture of your car', upload_to='car_avatars', storage=OverwriteStorage(), blank=True, null=True)
    thumb = m.ImageField('Thumbnail of your car', upload_to='car_thumbs', storage=OverwriteStorage(), blank=True, null=True)

    user_profile = m.ForeignKey(UserProfile, related_name="cars")
    
    @property
    def user(self): 
        return self.user_profile.user
    
    @property
    def car_str(self): 
        return "%s %s %s"%(self.year, self.make, self.model)   

    def __unicode__(self): 
        if self.year and self.make and self.model: 
            return "id: %d; %d %s %s"%(self.pk, self.year, self.make, self.model)
        else: 
            return "id: %s, empty car"%self.pk


class Lease(m.Model): 
    suggested_number = m.IntegerField("Suggested Number", null=True)
    suggested_race_class = m.ForeignKey('RaceClass', null=True, on_delete=m.SET_NULL, related_name='+')

    expiration = m.DateField("Expiration Date")
    permanent = m.BooleanField("Permanent Lease")

    user = m.ForeignKey(User, related_name="leases")
    car = m.ForeignKey("Car", related_name="leases")

    def __unicode__(self): 
        return "%s to %s"%(self.car.name, self.user.username)

#note this order is significant
clear_model_list = [Lease, Order, Coupon, Registration,
                    Membership, RaceClass, Dibs, Season, Event, 
                    Session, Result, Run, Location, Course, 
                    Car, Lease, User, Club]


def clear_db(): 
    print "Clearing the Database"
    for m in clear_model_list: 
        objs = m.objects.all().iterator()
        for o in objs: 
            o.delete()


