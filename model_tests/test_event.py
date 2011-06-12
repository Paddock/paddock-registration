import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Event, Registration, Season, Club

class TestEvent(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test"
        
        self.s = Season()
        self.s.year = 2011
        self.s.club = self.c
        self.s.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.season = self.s
        
    def tearDown(self): 
        self.s.delete()
        
    def testEventSafeName(self): 
        pass
    
    def testValidRegClose(self): 
        
        try: 
            self.e.reg_close = datetime.datetime.today()+datetime.timedelta(days=1)
            self.e.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'Registration must close before the date of the event.']}",str(err))
        else: 
            self.fail("ValidationError expected")
            
        
        
        
        
        