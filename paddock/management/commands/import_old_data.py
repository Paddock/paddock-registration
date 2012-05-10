import csv
from django.core.management.base import BaseCommand, CommandError

from paddock.models import Club

class Command(BaseCommand): 
    """imports data from paddock 1.0 database in csv file format""" 
    
    def handle(self, *args, **options):
        
        #read in clubs
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
