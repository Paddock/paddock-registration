import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m

from paddock.models import Registration, User, RaceClass, Event, Car, Club, \
                           Season, Session, Result, Run, UserProfile

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
        self.car.user_profile = self.user.get_profile()
        self.car.save()
        
        self.r = Registration()
        self.r.number = 11
        self.r.race_class = self.race_class
        self.r.pax_class = None
        self.r.event = self.e

        self.user_profile = UserProfile.objects.get(user=self.user)
        
    def tearDown(self): 
        
        for model in m.get_models(): 
            model.objects.all().delete()
    
    def test_calc_times_empty_results(self): 
        self.r.save()
        
        self.r.calc_times()
        
        self.assertEqual(self.r.total_raw_time,0)
        self.assertEqual(self.r.total_index_time,0)
        
    def test_calc_times(self): 
        self.r.save()        
        
        sess = Session()
        sess.name = "AM"
        sess.event = self.e
        sess.save()        
        
        res = Result()
        res.reg = self.r
        res.session = sess
        res.save()
        
        r = Run()
        r.base_time = 10.0
        r.result = res
        r.save()
        
        res = Result()
        res.reg = self.r
        res.session = sess
        res.save()
        
        r = Run()
        r.base_time = 10.0
        r.result = res
        r.save()
        
        self.r.save()
        self.r.calc_times()
        
        self.assertEqual(self.r.total_raw_time,20.0)
        self.assertEqual(self.r.total_index_time,self.r.total_raw_time*self.race_class.pax)
        
        
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
        self.r.user_profile = self.user_profile
        self.r.save()
        
        self.assertEqual("Justin",self.r.first_name)
        self.assertEqual("Gray",self.r.last_name)
        self.assertEqual("1990 Mazda Miata",self.r.car_name)
        
    def testAllowedNumberRaceClass(self): 
        
        self.r.car = self.car
        self.r.user_profile = self.user_profile
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
        
       
            
    def testMaxUserRegLimit(self): 
        self.e2 = Event()
        self.e2.name = "test event 2"
        self.e2.date = datetime.date.today() 
        self.e2.season = self.season
        self.e2.save()            
        
        self.race_class.user_reg_limit = 1
        self.race_class.save()
        
        self.r.car = self.car
        self.r.user_profile = self.user_profile
        self.r.event = self.e
        self.r.save()        
           
        self.r2 = Registration()
        self.r2.number = 11
        self.r2.race_class = self.race_class
        self.r2.pax_class = None
        self.r2.event = self.e2     
        self.r2.user_profile = self.user_profile
                
        try: 
            self.r2.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'You have reached the registration limit for CSP.']}",str(err))
        else: 
            self.fail("ValidationError expected")
              
            
    def testEventRegLimit(self):           
        self.race_class.event_reg_limit = 1
        self.race_class.save()
        
        self.r.car = self.car
        self.r.event = self.e
        self.r.save()        
                   
        self.r2 = Registration()
        self.r2.number = 111
        self.r2.race_class = self.race_class
        self.r2.pax_class = None
        self.r2.event = self.e    
        
        try: 
            self.r2.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'Only 1 registrations for CSP are "
                             "allowed for an event. The class is full']}",str(err))
        else: 
            self.fail("ValidationError expected") 
            
    def testCarDeleteFromReg(self): 
        """Check to make sure reg_car gets set to null if a car gets deleted"""
       
        self.r.car = self.car
        
        self.r.save()    
        
        self.assertEqual(self.r.car, self.car)
        
        self.car.delete()
        reg = Registration.objects.filter(number=11).get()
        
        self.assertIsNone(reg.car)
        
    def testMoveToBumpClass(self): 
        bump_class = RaceClass()
        bump_class.name = "Index"
        bump_class.pax = 1.0
        bump_class.club = self.c
        bump_class.save()
        
        self.r.bump_class = bump_class
        self.r.save()
        
        self.assertEqual(self.r.race_class,self.race_class)
        self.assertEqual(self.r.bump_class,bump_class)
        
    def testMakeAssocRegs(self): 
        e2 = Event()
        e2.name = "test event 2"
        e2.date = datetime.date.today() 
        e2.season = self.season
        e2.save()           
        
        self.e.child_events.add(e2)
        self.e.save()
       
        self.r.make_assoc_regs()
        regs = Registration.objects.filter(event=e2).all()
        self.assertEqual(len(regs),1)       
       
   
    def testUpdateAssocRegs(self): 
        e2 = Event()
        e2.name = "test event 2"
        e2.date = datetime.date.today() 
        e2.season = self.season
        e2.save()           
        
        self.e.child_events.add(e2)
        self.e.save()
       
        self.r.make_assoc_regs()
        
        self.r.number = 10
        self.r.save()
        self.r.update_assoc_regs()
        
        reg = Registration.objects.filter(event=e2).get()
        self.assertEqual(reg.number,self.r.number)
       