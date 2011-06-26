import datetime

from django.utils import unittest

from django.core.exceptions import ValidationError

from paddock.models import Club, Dibs, User, Season, Event, \
     Registration, RegDetail, RaceClass, Run, Result, Session

class TestDibs(unittest.TestCase): 
    
    def setUp(self): 
        
        self.c = Club()
        self.c.name = "test"
        self.c.events_for_dibs = 2
        
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
        self.e1.date = datetime.date(2011,5,1)
        self.e1.season = self.s
        self.e1.save()
        
        self.e2 = Event()
        self.e2.name = "event2"
        self.e2.date = datetime.date(2011,5,2)
        self.e2.season = self.s
        self.e2.save()
        
        self.e3 = Event()
        self.e3.name = "event3"
        self.e3.date = datetime.date(2011,5,2)
        self.e3.season = self.s
        self.e3.save()
        
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
            rd= RegDetail()
            rd.user = user
            rd.save()
            for j,event in enumerate(self.events): 
                if j<=i: 
                    r = Registration()
                    r.number = "%d%d"%(i+1,j+1)
                    r.race_class = self.race_class
                    r.pax_class = None
                    r.event = event    
                    r.reg_detail = rd
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
        
        self.assertEqual(len(self.c.dibs.all()),2)        
        
        
        
        