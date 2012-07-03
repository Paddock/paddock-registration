import datetime

from django.utils import unittest
import django.test
from django.core.exceptions import ValidationError

from paddock.models import Club, Season, Event, Session, \
     RaceClass, Registration, Result, Run

class TestSeasonBasic(django.test.TestCase): 
    """Test that don't use the test data"""
    
    def setUp(self):        
        self.c = Club()
        self.c.name = "test"
        
        self.s = Season()
        self.s.year = 2011
        self.s.club = self.c
        self.s.save()
        
        e = Event()
        e.name = "points event 0"
        e.date = datetime.date.today()-datetime.timedelta(days=10)
        
        self.s.events.add(e)    
        
        e.save()  
        
        e = Event()
        e.name = "points event 1"
        e.date = datetime.date.today()+datetime.timedelta(days=10)
        
        self.s.events.add(e)
        
        e.save()  
    
    
    def test_upcoming_events(self): 
        self.assertEqual(1,len(self.s.upcoming_events()))
            
        
class TestSeasonWithData(django.test.TestCase): 
    """test that use the large test dataset""" 
    
    fixtures = ['test_data.json']

    def test_events_with_results(self):       
        season = Season.objects.get(club___name="NORA - ASCC", year="2010")
        self.assertEqual(19,season.complete_events().count())
        self.assertEqual(0,season.upcoming_events().count())
        
        season = Season.objects.get(club___name="NORA - ASCC", year="2011")
        self.assertEqual(21,season.complete_events().count())
        self.assertEqual(21,season.complete_events().count())
        self.assertEqual(0,season.upcoming_events().count()) 
                         
                 