import datetime

from django.utils import unittest
import django.test
from django.core.exceptions import ValidationError

from paddock.models import Club, Season, Event, Session, \
     RaceClass, Registration, Result, Run

class TestSeasonBasic(django.test.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test"
        
        self.s = Season()
        self.s.year = 2011
        self.s.club = self.c
        self.s.save()
        
        self.e = Event()
        self.e.name = "points event 1"
        self.e.date = datetime.date.today()
        
        self.s.events.add(self.e)
        
        sess = Session()
        sess.name = "AM"
        sess.event = self.e
        sess.save()
        
        self.e.save()
            
    def testCountEventsWithResults(self): 
        
        self.assertEqual(0,self.s.count_events_with_results())     

        #create a bunch of fake results data
        race_class = RaceClass()
        race_class.name = "A"
        race_class.pax = 1
        race_class.club = self.c
        race_class.save()          
        
        #new event with 1 session
        e = Event()
        e.name = "points event 2"
        e.date = datetime.date.today()
        self.s.events.add(e)
        e.save()
        
        sess = Session()
        sess.name = "AM"
        sess.event = e
        sess.save()
        
        for i in range(0,4): 
            r = Registration()
            r.number = i
            r.race_class = race_class
            r._anon_f_name = "%d"%(i,)
            r.pax_class = None
            r.event = e
            r.full_clean()
            r.save()
            
            result = Result()
            result.reg = r
            result.session = sess
            result.save()
            for j in range(0,3): 
                run = Run()
                run.base_time = 100.0-i-j
                run.result = result
                run.save()     
        
        #new event with two sessions        
        e = Event()
        e.name = "points event 3"
        e.date = datetime.date.today()
        self.s.events.add(e)
        e.save()
        
        sess1 = Session()
        sess1.name = "AM"
        sess1.event = e
        sess1.save()
        
        sess2 = Session()
        sess2.name = "PM"
        sess2.event = e
        sess2.save()
        
        for i in range(0,4): 
            r = Registration()
            r.number = i
            r.race_class = race_class
            r._anon_f_name = "%d"%(i,)
            r.pax_class = None
            r.event = e
            r.full_clean()
            r.save()
            
            #result for first session
            result = Result()
            result.reg = r
            result.session = sess
            result.save()
            for j in range(0,3): 
                run = Run()
                run.base_time = 100.0-i-j
                run.result = result
                run.save() 
            
            #result for second session    
            result = Result()
            result.reg = r
            result.session = sess
            result.save()
            for j in range(0,3): 
                run = Run()
                run.base_time = 100.0-i-j
                run.result = result
                run.save()     
                 
                
        self.assertEqual(2,self.s.count_events_with_results())         