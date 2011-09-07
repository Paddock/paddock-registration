"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User

from paddock.models import find_user

from paddock.model_tests.test_club import TestClub
from paddock.model_tests.test_season import TestSeason
from paddock.model_tests.test_event import TestEvent, TestEventPointsCalc
from paddock.model_tests.test_registration import TestRegistration
from paddock.model_tests.test_coupon import TestCoupon
from paddock.model_tests.test_dibs import TestDibs
from paddock.model_tests.test_result import TestResult
from paddock.model_tests.test_membership import TestMembership
from paddock.model_tests.test_order_coupon import TestCoupon,TestOrder



class TestGeneral(TestCase): 
    
    def setUp(self): 
        self.u1 = User()
        self.u1.username = "user1" 
        self.u1.first_name = "Justin"
        self.u1.last_name = "Gray"  
        self.u1.set_password("test")
        
        self.u1.full_clean()
        self.u1.save()
        
        self.u2 = User()
        self.u2.username = "user2" 
        self.u2.first_name = "Scott"
        self.u2.last_name = "Gray"  
        self.u2.set_password("test")
        
        self.u2.full_clean()
        self.u2.save()
        
        self.u3 = User()
        self.u3.username = "user3" 
        self.u3.first_name = "Joe"
        self.u3.last_name = "Mauro" 
        
        self.u3.set_password("test")
        
        self.u3.full_clean()
        self.u3.save()
    
    def tearDown(self): 
        User.objects.all().delete()
        
    def testFindUser(self):     
        
        query = find_user('gray')
        self.assertEqual(set([self.u1,self.u2]),set(query))
        
        query = find_user('just')
        self.assertEqual(set([self.u1]),set(query))
        
        query = find_user('uro')
        self.assertEqual(set([self.u3]),set(query))
        
        query = find_user('user')
        self.assertEqual(set([self.u1,self.u2,self.u3]),set(query))
