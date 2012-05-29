import csv,datetime
from django.core.management.base import BaseCommand, CommandError

from paddock.models import Club, Season, Event, Registration, UserProfile, \
     RaceClass, Result, Session, Location, User

class Command(BaseCommand): 
    """imports data from paddock 1.0 database in csv file format""" 
    
    def handle(self, *args, **options):
        
        for line in csv.DictReader(open('old_data/driver.csv','rb')): 
            """user_name","email","verified","activation_code",
            "f_name","l_name","address","city","state",
            "zip_code","_password"""
            
            u = User.objects.create_user(line['user_name'],line['email'],"test") 
            
            u.password = "old_paddock$%s"%line['_password']
            u.save()
        exit()
        #read in clubs
        
        club_map = {}
        for line in csv.DictReader(open('old_data/club.csv','rb')): 
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
        
        location_map = {}    
        for line in csv.DictReader(open("old_data/location.csv")):    
                    """id","name","address","lat","lng","club_name"""''
                    club = Club.objects.get(_name=line['club_name'])        
                    
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
            club = Club.objects.get(_name=line['club_name'])
            s.club = club
            s.year = int(line['year'])
            s.drop_lowest_events = int(line['drop_lowest_events'])
            s.save()

            if bool(int(line['active'])): 
                club.active_season = s
            
            club.save()
            
            season_map[line['id']] = s

        event_map = {}
        for line in csv.DictReader(open('old_data/event.csv','rb')):
            
            """id","name","note","date","registration_close","member_cost",
            "non_member_cost","pay_at_event_cost","location_id","club_name",
            "season_id","multiplier","count_points"""
            
            
            e = Event()
            e.name = line['name']
            e.note = line['note']
            e.date = datetime.datetime.strptime(line['date'], '%Y-%m-%d %H:%M:%S')
            e.reg_close = datetime.datetime.strptime(line['registration_close'], '%Y-%m-%d %H:%M:%S')
            e.member_price = float(line['member_cost'])
            e.non_member_price = float(line['non_member_cost'])
            e.non_pre_pay_penalty = float(line['pay_at_event_cost'])
            #e.club = Club.objects.get(_name=line['club_name'])
            e.season = season_map[line['season_id']]
            e.count_points = int(line['count_points'])
            e.multiplier = int(line['multiplier'])
            
            print "test", line['location_id']
            if line['location_id'] != "NULL":
                print location_map[line['location_id']]
                e.location = location_map[line['location_id']]
            
            e.save()
            
            event_map[line['id']] = e
        
        race_class_map = {}
        for line in csv.DictReader(open('old_data/raceclass.csv')):
            """id","pax","name","club_name"""
            
            
            club = Club.objects.get(_name=line['club_name'])            
            
            
            r = RaceClass()
            r.name = line['name']
            r.pax = float(line['pax'])
            r.club = club
            
            r.save()
            
            race_class_map[line['id']] = r
            
        registration_map = {}    
        for line in csv.DictReader(open('old_data/registration.csv')): 
            
            """id","number","paid","token","payer_id","transaction_id",
            "price","class_points","index_points","index_flag","anon_f_name",
            "anon_l_name","anon_car","driver_user_name","event_id","reg_type_id",
            "car_id","race_class_id"""
            
            for k,v in line.iteritems(): 
                if v=="NULL": 
                    line[k] = ""
            if not line['event_id']: 
                continue 
            
            rc = race_class_map[line['race_class_id']]

            r = Registration()
            r.number = int(line['number'])
            r.paid = int(line['paid'])
            if line['price']:
                r.price = float(line['price'])
            else: 
                r.price = 0.00
            r.index_points = int(line['index_points'])
            r.class_points = int(line['class_points'])
            r._anon_car = line['anon_car']
            r._anon_l_name = line['anon_l_name']
            r._anon_f_name = line['anon_f_name']
            r.race_class = rc
            r.event = event_map[line['event_id']]
            #TODO reg_type_id
            #TODO car_id 
            #TODO race_class_id
            #TODO remove reg_detail class, and associate reg with UserProfile directly
            #TODO registrations can be siblings for joint update
            
            r.save()
            
            registration_map[line['id']] = r
        
        session_map = {}
        for line in csv.DictReader(open('old_data/session.csv')):
            "id","name","event_id","course_id"
            
            try: 
                event_map[line['event_id']]
            except: 
                continue
            
            s = Session()
            s.name = line['name']
            s.event = event_map[line['event_id']]
            s.save()
            
            session_map[line['id']] = s
            
        result_map = {}    
        for line in csv.DictReader(open('old_data/result.csv')):        
            "id","registration_id","event_id","sess_id"
            try: 
                registration_map[line['registration_id']]
                session_map[line['sess_id']]
            except: 
                continue
            
            r = Result()
            r.reg = registration_map[line['registration_id']]
            r.session = session_map[line['sess_id']]
            r.save()
            
            result_map[line['id']] = r
            
        
