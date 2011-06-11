import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Club, Season, Event

class TestSeason(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test"
        
        self.s = Season()
        self.s.year = 2011
        
        self.e = Event()
        self.e.name = "points event 1"
        self.e.date = datetime.date.today()
        
        self.s.events.add(self.e)
    
    def testCountEventResults(self):    
        self.assertEqual(0,self.s.count_events_with_results())      
        