import csv,datetime
from django.core.management.base import BaseCommand, CommandError

from paddock.models import Club, Season, Event

class Command(BaseCommand): 
    """imports data from paddock 1.0 database in csv file format""" 
    
    def handle(self, *args, **options):
        
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
            
        season_map = {}    
        for line in csv.DictReader(open('old_data/season.csv')): 
            s = Season()
            
            """"id","year","active","club_name","drop_lowest_events"""
            
            s.club = Club.objects.get(_name=line['club_name'])
            s.year = int(line['year'])
            s.drop_lowest_events = int(line['drop_lowest_events'])
            
            s.save()
            
            season_map[line['id']] = s
            
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
            e.count_points = bool(line['count_points'])
            e.multiplier = int(line['multiplier'])
            
            #TODO: Location stuff
            
            e.save()
            
            
            
