import csv
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand): 
    """imports data from paddock 1.0 database in csv file format""" 
    
    def handle(self, *args, **options):
        
        #read in clubs
    for line in csv.DictReader(open(''))
        

