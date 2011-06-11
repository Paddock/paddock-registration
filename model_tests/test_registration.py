import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Registration, User, RaceClass, Event, Car, Club

class TestRegistration(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test club"
        self.c.full_clean()
        self.c.save()
        
        self.race_class = RaceClass()
        self.race_class.name = "CSP"
        self.race_class.pax = .875
        self.race_class.club = self.c
        self.race_class.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.save()
        
        self.user = User()
        self.user.first_name = "Justin"
        self.user.last_name = "Gray"
        self.user.save()
        
        self.car = Car()
        self.car.year = 1990 
        self.car.make = "Mazda"
        self.car.model = "Miata"
        self.car.owner = self.user
        self.car.save()
        
        self.r = Registration()
        self.r.number = 11
        self.r.race_class = self.race_class
        self.r.pax_class = None
        self.r.event = self.e
        
    def tearDown(self): 
        
        self.r.delete()
        self.e.delete()
        self.car.delete()
        self.user.delete()
        self.race_class.delete()
        self.c.delete()
        
        
        
    def testAnon(self): 
        
        self.r._anon_f_name = "Justin"
        self.r._anon_l_name = "Gray" 
        self.r._anon_car = "1990 Mazda Miata"
        
        self.r.save()
        
        self.assertEqual("Justin",self.r.first_name)
        self.assertEqual("Gray",self.r.last_name)
        self.assertEqual("1990 Mazda Miata",self.r.car_name)
        
    def testWithCar(self): 
        
        self.r.car = self.car
        self.r.user = self.user
        
        self.r.save()
        
        self.assertEqual("Justin",self.r.first_name)
        self.assertEqual("Gray",self.r.last_name)
        self.assertEqual("1990 Mazda Miata",self.r.car_name)
        