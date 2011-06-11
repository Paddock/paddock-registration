import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Event

class TestEvent(unittest.TestCase): 
    
    def setUp(self): 
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
    
    def testValidRegClose(self): 
        
        try: 
            self.e.reg_close = datetime.datetime.today()+datetime.timedelta(days=1)
            self.e.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'Registration must close before the date of the event.']}",str(err))
        else: 
            self.fail("ValidationError expected")
        
        