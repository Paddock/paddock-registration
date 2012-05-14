import datetime

from django.utils import unittest

from django.core.exceptions import ValidationError

from paddock.models import Club, Dibs, User, Season, Event, \
     Registration, RaceClass, Run, Result, Session, \
     clean_dibs, UserProfile

class TestDibs(unittest.TestCase): 
    
    def setUp(self): 
        
        self.today = datetime.date.today()
        
        self.c = Club()
        self.c.name = "test"
        self.c.events_for_dibs = 2
        self.c.save()
        
        self.race_class = RaceClass()
        self.race_class.name = "CSP"
        self.race_class.pax = .875
        self.race_class.club = self.c
        self.race_class.save()
        
        self.s = Season()
        self.s.year = 2011
        self.s.club = self.c
        self.s.save()
        
        self.e1 = Event()
        self.e1.name = "event1"
        self.e1.date = self.today-datetime.timedelta(days=10)
        self.e1.season = self.s
        self.e1.save()
        
        self.e2 = Event()
        self.e2.name = "event2"
        self.e2.date = self.today-datetime.timedelta(days=8)
        self.e2.season = self.s
        self.e2.save()
        
        self.e3 = Event()
        self.e3.name = "event3"
        self.e3.date = self.today-datetime.timedelta(days=5)
        self.e3.season = self.s
        self.e3.save()
        
        self.e4 = Event()
        self.e4.name = "event4"
        self.e4.date = self.today+datetime.timedelta(days=10)
        self.e4.season = self.s
        self.e4.save()
        
        self.events = [self.e1,self.e2,self.e3]       
        
        for event in self.events: 
            s = Session()
            s.event = event
            s.name = "AM"
            s.save()
        
        self.u1 = User()
        self.u1.username = "user1"
        self.u1.save()
        
        self.u2 = User()
        self.u2.username = "user2"
        self.u2.save()
        
        self.u3 = User()
        self.u3.username = "user3"
        self.u3.save()
        
        self.users = [self.u1,self.u2,self.u3]
        
        for i,user in enumerate(self.users): 
            up = user.get_profile()
            for j,event in enumerate(self.events): 
                if j<=i: 
                    r = Registration()
                    r.number = "%d"%(i+1)
                    r.race_class = self.race_class
                    r.pax_class = None
                    r.event = event    
                    r.user_profile = up
                    r.save()
                    
                    result = Result()
                    result.reg = r
                    result.session = event.sessions.all()[0]
                    result.save()
                    
                    for k in range(0,3):
                        r = Run()
                        r.base_time = 10.0
                        r.calc_time = 10.0
                        r.index_time = 10.0
                        r.result = result
                        r.save()

                        
    def tearDown(self): 
        self.u3.delete()
        self.u2.delete()
        self.u1.delete()
        self.s.delete()
        self.c.delete()
        
    def test_1_dibs(self): 
        
        self.c.assign_dibs()
        
        self.assertEqual(len(self.c.dibs.filter(club=self.c,user_profile=self.u3.get_profile()).all()),1) 
        dibs = Dibs.objects.filter(club=self.c,user_profile=self.u3.get_profile()).get()
        self.assertEqual(dibs.number,3)
        self.assertEqual(dibs.race_class,self.race_class)
        self.assertEqual(dibs.expires,self.e4.date+datetime.timedelta(days=30))
        
        Dibs.objects.all().delete()
        
    def test_no_dibs(self): 
        reg = Registration()
        up = UserProfile.objects.get(user=self.u1)
        reg.user_profile = up
        reg.number = 15
        reg.race_class = self.race_class
        reg.pax_class = None
        reg.event = self.e4
        reg.save()   
        
        s = Session()
        s.event = self.e4
        s.name = "AM"
        s.save()
        
        result = Result()
        result.reg = reg
        result.session = s
        result.save()
        
        for k in range(0,3):
            r = Run()
            r.base_time = 10.0
            r.calc_time = 10.0
            r.index_time = 10.0
            r.result = result
            r.save()        
        
        self.c.assign_dibs()
        self.assertEqual(len(Dibs.objects.all()),0) 
                        
        reg.delete()
        s.delete()
        
    def test_no_result_reg_dibs(self): 
        reg = Registration()
        up = UserProfile.objects.get(user=self.u2)
        reg.user_profile = up
        reg.number = 15
        reg.race_class = self.race_class
        reg.pax_class = None
        reg.event = self.e3
        reg.save() 
        
        self.c.assign_dibs()
        
        self.assertEqual(len(self.c.dibs.filter(club=self.c,user_profile=self.u3.get_profile()).all()),1) 
        dibs = Dibs.objects.filter(club=self.c,user_profile=self.u3.get_profile).get()
        self.assertEqual(dibs.number,3)
        self.assertEqual(dibs.race_class,self.race_class)
        self.assertEqual(dibs.expires,self.e4.date+datetime.timedelta(days=30))
        
        reg.delete()
        Dibs.objects.all().delete()
        
    def test_update_existing_dibs(self):
        
        dibs = Dibs()
        dibs.club = self.c
        dibs.user_profile = self.u3.get_profile()
        dibs.race_class = self.race_class
        dibs.number = 3
        dibs.duration = 30
        dibs.expires = self.today+datetime.timedelta(days=5)
        dibs.save()
        dibs.created = self.today-datetime.timedelta(days=60)
        dibs.save()
        
        self.c.assign_dibs()       
        self.assertEqual(len(self.c.dibs.filter(club=self.c,user_profile=self.u3.get_profile()).all()),1) 
        dibs = Dibs.objects.filter(club=self.c,user_profile=self.u3.get_profile()).get()
        self.assertEqual(dibs.duration,60)
        self.assertEqual(dibs.expires,self.e3.date+datetime.timedelta(days=60))
        
        dibs.delete()
        
    def test_dont_update_old_dibs(self): 
        
        dibs = Dibs()
        dibs.club = self.c
        dibs.user_profile = self.u1.get_profile()
        dibs.race_class = self.race_class
        dibs.number = 3
        dibs.duration = 30
        dibs.expires = self.today-datetime.timedelta(days=5)
        dibs.save()
        dibs.created = self.today-datetime.timedelta(days=60)
        dibs.save()
        
        self.c.assign_dibs()  
        
        dibs = Dibs.objects.filter(user_profile=self.u1.get_profile()).get()
        
        self.assertEqual(dibs.expires,self.today-datetime.timedelta(days=5))
        self.assertEqual(dibs.duration,30)
        
    def test_race_class_allow_dibs(self): 
        
        self.race_class.allow_dibs = False
        self.race_class.save()
        
        self.c.assign_dibs()
        
        self.assertEqual(len(Dibs.objects.all()),0)
        
    def test_clean_dibs(self): 
        
        dibs = Dibs()
        dibs.club = self.c
        dibs.expires = datetime.date.today()-datetime.timedelta(days=10)
        dibs.duration = 30
        dibs.number = 99
        dibs.race_class = self.race_class
        dibs.user_profile = self.u2.get_profile()
        
        dibs.save()

        clean_dibs()
        
        self.assertEqual(len(self.c.dibs.filter(club=self.c,user_profile=self.u3.get_profile()).all()),1) 
        dibs = Dibs.objects.filter(club=self.c,user_profile=self.u3.get_profile()).get()
        self.assertEqual(dibs.number,3)
        self.assertEqual(dibs.race_class,self.race_class)
        self.assertEqual(dibs.expires,self.e4.date+datetime.timedelta(days=30))
        
        self.assertEqual(len(self.c.dibs.filter(club=self.c,user_profile=self.u2.get_profile()).all()),0) 
        
    def test_race_class_allow_dibs(self): 
        
        self.race_class.allow_dibs = False
        self.race_class.save()
        
        self.c.assign_dibs()
        
        self.assertEqual(len(Dibs.objects.all()),0)
        
        
        
        
        
        
        
        
        
        
        