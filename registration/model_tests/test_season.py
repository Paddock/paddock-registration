import datetime

from django.utils import unittest
import django.test
from django.core.exceptions import ValidationError

from registration.models import Club, Season, Event, Session, \
     RaceClass, Registration, Result, Run


class TestSeasonBasic(django.test.TestCase): 
    """Test that don't use the test data"""
    
    def setUp(self):        
        self.c = Club()
        self.c.name = "test"
        self.c.save()
        
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
        self.assertEqual(1, len(self.s.upcoming_events()))
            
        
class TestSeasonWithData(django.test.TestCase): 
    """test that use the large test dataset""" 
    
    fixtures = ['test_data.json', ]

    def test_events_with_results(self):  
        #print Season.objects.all()
        season = Season.objects.get(club__name="NORA - ASCC", year="2010")
        self.assertEqual(19, season.complete_events().count())
        self.assertEqual(0, season.upcoming_events().count())
        
        season = Season.objects.get(club__name="NORA - ASCC", year="2011")
        self.assertEqual(21, season.complete_events().count())
        self.assertEqual(21, season.complete_events().count())
        self.assertEqual(0, season.upcoming_events().count()) 
 
        index_points, class_points = season.points_as_of()     
        self.assertEqual(26044, index_points[0][1]['points'])
        self.assertEqual(12, index_points[0][1]['n_regs'])
        
        self.assertEqual(22456, index_points[2][1]['points'])
        self.assertEqual(12, index_points[2][1]['n_regs'])
        
        self.assertEqual(19835, index_points[6][1]['points'])
        self.assertEqual(12, index_points[6][1]['n_regs'])        
           
        self.assertEqual("AM", class_points[0][0].abrv)
        self.assertEqual("AS", class_points[1][0].abrv)
        self.assertEqual(49, class_points[1][1][0][1]['points'])
        
        pe8_date = datetime.date(2011, 7, 17)
        index_points, class_points = season.points_as_of(pe8_date)
        
        self.assertEqual(17216, index_points[0][1]['points'])
        self.assertEqual(8, index_points[0][1]['n_regs'])
        
        self.assertEqual(14471, index_points[2][1]['points'])
        self.assertEqual(7, index_points[2][1]['n_regs'])
        
        self.assertEqual(12676, index_points[6][1]['points'])
        self.assertEqual(7, index_points[6][1]['n_regs']) 
        
        self.assertEqual("AM", class_points[0][0].abrv)
        self.assertEqual("AS", class_points[1][0].abrv)
        self.assertEqual(43, class_points[1][1][0][1]['points'])        
        
        