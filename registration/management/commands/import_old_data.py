import csv
import datetime
from os.path import exists
from django.core.management.base import BaseCommand
from django.core.files import File
from registration.models import Club, Season, Event, Registration, \
     RaceClass, Result, Session, Location, User, Car, Run, Coupon, \
     Membership


class Command(BaseCommand): 
    """imports data from paddock 1.0 database in csv file format""" 
    
    def handle(self, *args, **options):
        reader = csv.DictReader(open('old_data/driver.csv', 'rU'))
        for line in reader: 
            """user_name","email","verified","activation_code",
            "f_name","l_name","address","city","state",
            "zip_code","_password"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None   
                             
            u = User()
            u.username = line['user_name']
            u.email = line['email']
            u.password = "old_paddock$%s"%line['_password']
            u.first_name = line['f_name']
            u.last_name = line['l_name']
            u.is_active = True
            u.save()
            
            up = u.get_profile()
            up.address = line['address']
            up.city = line['city']
            up.state = line['state']
            up.zip_code = line['zip_code']
            up.save()
            
        #dev to make it so I can login to any account    
        justin = User.objects.get(username="justingray")   
        password = justin.password
        
        User.objects.all().update(password=password)

        car_map = {}
        reader = csv.DictReader(open('old_data/car.csv', 'rb'))
        for line in reader:     
            """id","nickname","make","model","color","avatar_file_loc",
            "avatar_thumb_loc","year","owner_user_name"""
            for k,v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
            if line['owner_user_name']: 
                try: 
                    c = Car()
                    c.provisional = False;
                    c.name = line['nickname']
                    c.make = line['make']
                    c.model = line['model']
                    if line['color']: c.color = line['color']
                    c.year = line['year']
                    c.user_profile = User.objects.get(username=line['owner_user_name']).get_profile()
                    s_car_id = (line['owner_user_name'],line['nickname'])
                    if exists('old_data/avatars/%s_%s_avatar'%s_car_id): 
                        c.avatar.save('%s_%s_avatar'%s_car_id,File(open('old_data/avatars/%s_%s_avatar'%s_car_id)))
                        c.thumb.save('%s_%s_thumb'%s_car_id,File(open('old_data/avatars/%s_%s_thumb'%s_car_id)))
                    c.save()
                    car_map[line['id']] = c
                except:
                    continue         
                    
        
        #read in clubs
        
        club_map = {}
        for line in csv.DictReader(open('old_data/club.csv','rU')): 
            """"name","web_link","process_payments","points_calc_type",
            "membership_cost","renewal_cost","membership_terms","paypal_email",
            "index_point_method","address","city","state","zip_code","""
            for k,v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
            c = Club()
            c.city = line['city']
            c.address = line['address']
            c.zip_code = line['zip_code']
            c.state = line['state']
            c.name = line['name']
            c.process_payments = line['process_payments']
            c.paypal_email = line['paypal_email']
            c.membership_terms = line['membership_terms']
            c.new_member_cost = line['membership_cost']
            c.renew_cost = line['renewal_cost']

            c.save()

            club_map[line['name']] = c

        for line in csv.DictReader(open('old_data/coupon.csv')):    
            """coupon_code","club_name","discount_amount","uses_left","expires",
            "permanent","driver_user_name","registration_id"""    
            for k,v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None
            
            c = Coupon()
            c.code = line['coupon_code']
            c.permanent = bool(line['permanent'])
            c.club = club_map[line['club_name']]
            c.uses_left = line['uses_left']
            c.discount_amount = line['discount_amount']
            if line['expires']: 
                c.expires = datetime.datetime.strptime(line['expires'], '%Y-%m-%d %H:%M:%S')
            if line['driver_user_name']:
                c.user_prof = User.objects.get(username=line['driver_user_name']).get_profile()
            c.save()    

        reader = csv.DictReader(open('old_data/membership.csv', 'rb'))
        for line in reader: 
            """"id","club_name","number","start_date","valid_thru_date",
            "price","paid","token","payer_id","transaction_id","anon_f_name",
            "anon_l_name","driver_user_name"""
            
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None 

            m = Membership()
            m.num = line['number']

            m.start = datetime.datetime.strptime(line['start_date'], '%Y-%m-%d %H:%M:%S')
            m.valid_thru = datetime.datetime.strptime(line['valid_thru_date'], '%Y-%m-%d %H:%M:%S')
            m.paid = bool(line['paid'])
            if line['price']!=None:
                m.price = float(line['price'])

            try: 
                m.user_prof = User.objects.get(username=line['driver_user_name']).get_profile()
            except User.DoesNotExist: 
                continue    
            m.club = club_map[line['club_name']]
            
            m._anon_f_name = line['anon_f_name']
            m._anon_l_name = line['anon_l_name']

            m.save()
        
        location_map = {}    
        for line in csv.DictReader(open("old_data/location.csv")):    
                """id","name","address","lat","lng","club_name"""
                for k, v in line.iteritems(): 
                    if v == "NULL": 
                        line[k] = None                
                club = Club.objects.get(name=line['club_name'])        
                
                l = Location()
                l.name = line['name']
                l.address = line['address']
                #l.lat = line['lat']
                #l.lon = line['lng']
                l.club = club
                
                l.save()      
                
                location_map[line['id']] = l
                    
        season_map = {}    
        for line in csv.DictReader(open('old_data/season.csv')): 
            s = Season()
            """"id","year","active","club_name","drop_lowest_events"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
            club = Club.objects.get(name=line['club_name'])
            s.club = club
            s.year = int(line['year'])
            s.drop_lowest_events = int(line['drop_lowest_events'])
            s.save()
            
            club.save()
            
            season_map[line['id']] = s

        event_map = {}
        for line in csv.DictReader(open('old_data/event.csv', 'rU')):
            
            """id","name","note","date","registration_close","member_cost",
            "non_member_cost","pay_at_event_cost","location_id","club_name",
            "season_id","multiplier","count_points"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
            
            e = Event()
            e.name = line['name']
            e.note = line['note']
            e.date = datetime.datetime.strptime(line['date'], '%Y-%m-%d %H:%M:%S')
            e.reg_close = line['registration_close']+"-05:00"
            e.member_price = float(line['member_cost'])
            e.non_member_price = float(line['non_member_cost'])
            e.non_pre_pay_penalty = float(line['pay_at_event_cost'])
            e.season = season_map[line['season_id']]
            e.club = e.season.club
            e.count_points = int(line['count_points'])
            e.multiplier = int(line['multiplier'])
            
            if line['location_id']:
                e.location = location_map[line['location_id']]
            
            e.save()
            
            event_map[line['id']] = e
        
        race_class_map = {}
        for line in csv.DictReader(open('old_data/raceclass.csv')):
            """id","pax","name","club_name"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
            
            club = Club.objects.get(name=line['club_name'])                        
            r = RaceClass()
            r.name = line['name']
            r.abrv = line['name']
            r.pax = float(line['pax'])
            r.club = club
            r.save()
            
            race_class_map[line['id']] = r
            
        index_class = RaceClass()
        index_class.name = 'Index'
        index_class.bump_class = True
        index_class.abrv = "i"
        index_class.pax = 1.0
        index_class.club = club
        index_class.save()
        
        reg_type_map = {}    
        for line in csv.DictReader(open('old_data/regtype.csv')):
            """id","name","class_letters","reg_limit","index",
            "description","club_name"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
            club = Club.objects.get(name=line['club_name']) 
            r = RaceClass()
            r.pax_class = True
            r.description = line['description']
            r.name = line['name']
            r.abrv = line['class_letters']
            if line['reg_limit']: 
                r.user_reg_limit=line['reg_limit']
            r.pax = 1.0
            r.club = club
            r.save()
            
            reg_type_map[line['id']] = r
        
        registration_map = {}  
        for line in csv.DictReader(open('old_data/registration.csv')): 
            
            """id","number","paid","token","payer_id","transaction_id",
            "price","class_points","index_points","index_flag","anon_f_name",
            "anon_l_name","anon_car","driver_user_name","event_id","reg_type_id",
            "car_id","race_class_id"""
            
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None            
                
            if not line['event_id']: 
                continue            
            
            rc = race_class_map[line['race_class_id']]

            r = Registration()

            r.paid = bool(line['paid'])
            if line['price']!=None:
                r.price = float(line['price'])
            
            if line['driver_user_name']: 
                user = User.objects.get(username=line['driver_user_name'])
                r.user_profile = user.get_profile()
            r.number = int(line['number'])
            r.paid = int(line['paid'])
            r.index_points = line['index_points']
            r.class_points = line['class_points']
            if line['price']:
                r.price = float(line['price'])
            else: 
                r.price = 0.00
            r.index_points = int(line['index_points'])
            r.class_points = int(line['class_points'])
            if line['anon_car']: 
                r._anon_car=line['anon_car'].strip()
            if line['anon_l_name']: 
                r._anon_l_name=line['anon_l_name'].strip()
            if line['anon_f_name']: 
                r._anon_f_name=line['anon_f_name'].strip()
            r.race_class = rc
            r.event = event_map[line['event_id']]
            r.club = r.event.club
            try: 
                if line['reg_type_id']: 
                    r.pax_class=reg_type_map[line['reg_type_id']]
            except: 
                pass
            
            if line['index_flag']: 
                r.bump_class=index_class
            try: 
                if line['car_id']:
                    r.car=car_map[line['car_id']]
            except: 
                pass
            #TODO race_class_id
            #TODO remove reg_detail class, and associate reg with UserProfile directly
            #TODO registrations can be siblings for joint update
            
            r.save()
            
            registration_map[line['id']] = r
                
        session_map = {}
        for line in csv.DictReader(open('old_data/session.csv')):
            """id", "name", "event_id", "course_id"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None             
            
            try: 
                event_map[line['event_id']]
            except: 
                continue
            
            s = Session()
            s.name = line['name']
            s.event = event_map[line['event_id']]
            s.club = s.event.club
            s.save()
            
            session_map[line['id']] = s
            
        result_map = {}    
        for line in csv.DictReader(open('old_data/result.csv')):        
            """id","registration_id","event_id","sess_id"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None                        
    
            try: 
                registration_map[line['registration_id']]
                session_map[line['sess_id']]
            except: 
                continue
            
            r = Result()
            r.reg = registration_map[line['registration_id']]
            r.session = session_map[line['sess_id']]
            r.club = r.session.club
            r.save()
            
            result_map[line['id']] = r
            
        for line in csv.DictReader(open('old_data/run.csv')):
            """id","base_time","calc_time","index_time","cones",
            "penalty","result_id","result_2_id"""
            for k, v in line.iteritems(): 
                if v == "NULL": 
                    line[k] = None
                    
            if line['base_time'] == None: 
                continue
            try: 
                r = Run()
                r.base_time = float(line['base_time'])
                r.cones = int(line['cones'])
                if line['penalty']:
                    r.penalty = line['penalty']
                r.result = result_map[line['result_id']]
                r.club = r.result.club
                r.save()
                
            except KeyError: 
                continue


        for reg in Registration.objects.select_related('results').all(): 
            reg.calc_times()