from django.core.management.base import BaseCommand
from registration.models import Car


class Command(BaseCommand): 
    """imports data from paddock 1.0 database in csv file format""" 
    
    def handle(self, *args, **options):

        provisional_cars = Car.objects.filter(provisional=True).all().delete()


        