import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m

from registration.models import Club, User, Membership

class TestMembership(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test club"
        self.c.full_clean()
        self.c.save()
        
        self.user1 = User()
        self.user1.first_name = "Justin"
        self.user1.last_name = "Gray"
        self.user1.username = "justingray"
        self.user1.save()
        
        self.user2 = User()
        self.user2.first_name = "Sirius"
        self.user2.last_name = "Gray"
        self.user2.username = "tito"
        self.user2.save()
        
        m= Membership()
        m.user = self.user1
        m.club = self.c
        m.num = 1
        m.start = datetime.date.today() - datetime.timedelta(days=300)
        m.valid_thru = datetime.date.today()+datetime.timedelta(days=1)
        
        m.full_clean()
        m.save()
        
    def tearDown(self): 
        
        for model in m.get_models(): 
            model.objects.all().delete()
            
    def test_is_active_member(self):         
        self.assertTrue(self.c.is_active_member(self.user1))
        self.assertFalse(self.c.is_active_member(self.user2))
        
        m= Membership()
        m.user = self.user2
        m.club = self.c
        m.num = 2
        m.start = datetime.date.today() - datetime.timedelta(days=300)
        m.valid_thru = datetime.date.today()
        
        m.full_clean()
        m.save()
        
        #make sure expired memberships don't report as active
        self.assertFalse(self.c.is_active_member(self.user2))
        
    
    def test_duplicate_id(self): 
        m= Membership()
        m.user = self.user2
        m.club = self.c
        m.num = 1
        m.start = datetime.date.today() - datetime.timedelta(days=300)
        m.valid_thru = datetime.date.today()+datetime.timedelta(days=1)
        
        try: 
            m.full_clean()
            m.save()
        except ValidationError as err: 
            self.assertEqual(str(err),"{'__all__': [u'A member with that number already exists']}")
        else: 
            self.fail("ValidationError expected")
    
    def test_auto_increment_number(self): 
        m= Membership()
        m.user = self.user2
        m.club = self.c
        m.start = datetime.date.today() - datetime.timedelta(days=300)
        m.valid_thru = datetime.date.today()
        
        m.full_clean()
        m.save()
        
        self.assertEqual(m.num,2)