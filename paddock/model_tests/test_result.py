import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Registration, User, RaceClass, Event, Car, Club, \
                           Season, Result, Run, Session


class TestResult(unittest.TestCase): 
    
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
        
        self.sess = Session()
        self.sess.name = "AM"
        self.sess.event = self.e
        self.sess.save()
        
        
        self.r = Registration()
        self.r.number = 11
        self.r.race_class = self.race_class
        self.r.pax_class = None
        self.r.event = self.e
        self.r.save()
        
        self.result = Result()
        self.result.reg = self.r
        self.result.session = self.sess
        self.result.save()
        
    def tearDown(self): 
        
        Club.objects.all().delete()
        Season.objects.all().delete()
        RaceClass.objects.all().delete()
        Event.objects.all().delete()
        Session.objects.all().delete()
        Registration.objects.all().delete()
        Result.objects.all().delete()
        Run.objects.all().delete()
    
    def test_best_run1(self): 
        
        r1 = Run()
        r1.base_time = 10.0
        r1.result = self.result
        r1.save()
        
        r2 = Run()
        r2.base_time = 11.0
        r2.result = self.result
        r2.save()
        
        r3 = Run()
        r3.base_time = 9.0
        r3.cones = 1
        r3.result = self.result
        r3.save()
        
        r4 = Run()
        r4.base_time = 10.0
        r4.result = self.result
        r4.penalty = "DNF"
        r4.save()
        
        
        best_run = self.result.find_best_run()
        
        self.assertEqual(best_run,r1)
        
    def test_best_run2(self): 
        
        r1 = Run()
        r1.base_time = 10.0
        r1.result = self.result
        r1.save()
        
        
        best_run = self.result.find_best_run() 
        
        self.assertEqual(best_run,r1)   
        
        
    def test_best_run3(self): 
        
        r1 = Run()
        r1.base_time = 10.0
        r1.result = self.result
        r1.save()
        
        r2 = Run()
        r2.base_time = 9.0
        r2.result = self.result
        r2.save()
        
        r3 = Run()
        r3.base_time = 10.5
        r3.result = self.result
        r3.save()
        
        
        best_run = self.result.find_best_run() 
        
        self.assertEqual(best_run,r2) 
        
        
        
        
    def test_best_run_no_clean_runs(self): 
        
        r1 = Run()
        r1.base_time = 10.0
        r1.result = self.result
        r1.penalty = "DNF"
        r1.save()
        
        r2 = Run()
        r2.base_time = 0.1
        r2.result = self.result
        r2.penalty = "O/C"
        r2.save()
        
        best_run = self.result.find_best_run() 
        
        self.assertEqual(best_run,None)        
    