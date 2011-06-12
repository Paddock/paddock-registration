import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Registration, User, RaceClass, Event, Car, Club, \
                           RegDetail, Season

class TestRegistration(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test club"
        self.c.full_clean()
        self.c.save()
        
        self.season = Season()
        self.season.club = self.c
        self.season.year = 2011
        self.season.save()
        
        self.race_class = RaceClass()
        self.race_class.name = "CSP"
        self.race_class.pax = .875
        self.race_class.club = self.c
        self.race_class.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.season = self.season
        self.e.save()
        
        self.user = User()
        self.user.first_name = "Justin"
        self.user.last_name = "Gray"
        self.user.username = "justingray"
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
        
        self.reg_detail = RegDetail()
        self.reg_detail.user = self.user
        self.reg_detail.save()
        
    def tearDown(self): 
        
        try: 
            self.r.delete()
        except AssertionError: 
            pass 
        
        self.e.delete()
        self.car.delete()
        self.user.delete()
        self.race_class.delete()
        self.c.delete()
        self.season.delete()
        self.reg_detail.delete()
        
        
        
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
        self.r.reg_detail = self.reg_detail
        
        self.reg_detail.save()
        self.r.save()
        
        self.assertEqual("Justin",self.r.first_name)
        self.assertEqual("Gray",self.r.last_name)
        self.assertEqual("1990 Mazda Miata",self.r.car_name)
        
    def testAllowedNumberRaceClass(self): 
        
        self.r.car = self.car
        self.r.reg_detail = self.reg_detail

        self.r.save()        
        
        self.r2 = Registration()
        self.r2.number = 11
        self.r2.race_class = self.race_class
        self.r2.pax_class = None
        self.r2.event = self.e
        
        try: 
            self.r2.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'11 CSP is already taken, pick another number.']}",str(err))
        else: 
            self.fail("ValidationError expected")
            
        self.e2 = Event()
        self.e2.name = "test event 2"
        self.e2.date = datetime.date.today()  
        self.e2.season = self.season
        self.e2.save()        
        
        self.r3 = Registration()
        self.r3.number = 77
        self.r3.race_class = self.race_class
        self.r3.pax_class = None
        self.r3.event = self.e2
        self.r3.save()
        
        self.e.child_events.add(self.e2)
        self.e.save()
        
        self.r2.number = 77
        
        try: 
            self.r2.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'77 CSP is already taken, pick another number.']}",str(err))
        else: 
            self.fail("ValidationError expected")
        
        self.e2.delete()
        self.r3.delete()
            
    def testMaxUserRegLimit(self): 
        self.e2 = Event()
        self.e2.name = "test event 2"
        self.e2.date = datetime.date.today() 
        self.e2.season = self.season
        self.e2.save()            
        
        self.race_class.user_reg_limit = 1
        self.race_class.save()
        
        self.r.car = self.car
        self.r.reg_detail = self.reg_detail
        self.r.event = self.e
        self.r.save()        
           
        self.r2 = Registration()
        self.r2.number = 11
        self.r2.race_class = self.race_class
        self.r2.pax_class = None
        self.r2.event = self.e2     
        self.r2.reg_detail = self.reg_detail
                
        try: 
            self.r2.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'You have reached the registration limit for CSP.']}",str(err))
        else: 
            self.fail("ValidationError expected")
            
        self.e2.delete()
            
            
    def testEventRegLimit(self):           
        self.race_class.event_reg_limit = 1
        self.race_class.save()
        
        self.r.car = self.car
        self.r.reg_detail = self.reg_detail
        self.r.event = self.e
        self.r.save()        
                   
        self.r2 = Registration()
        self.r2.number = 111
        self.r2.race_class = self.race_class
        self.r2.pax_class = None
        self.r2.event = self.e    
        self.r2.reg_detail = self.reg_detail
        
        try: 
            self.r2.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'Only 1 registrations for CSP are "
                             "allowed for this event. The class is full']}",str(err))
        else: 
            self.fail("ValidationError expected")  