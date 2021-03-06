import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m
from django.core import mail


from registration.models import (Registration, User, Club,
     Coupon, Order, Membership, Season, Event, RaceClass, 
     clear_db
     )


class TestCoupon(unittest.TestCase):   
    
    def tearDown(self): 
        clear_db()
            
    def test_validcode(self): 
        c = Coupon()
        c.code = "test code"

        club = Club()
        club.name = "test-test"
        club.save()
        c.club = club
        
        try: 
            c.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'code': [u'Spaces not allowed in the code']}", str(err))
        else: 
            self.fail("ValidationError expected")

    def test_expires(self):  
        c = Coupon()
        c.expires = datetime.date.today()
        c.code = "testcode"

        club = Club()
        club.name = "test-test"
        club.save()
        c.club = club

        try: 
            c.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'expires': [u'Date must be at least one day from now']}", str(err))
        else: 
            self.fail("ValidationError expected")   

              
        
    def test_discount_calculation(self): 
        c = Coupon()
        c.discount_amount = "10.00"
        
        self.assertEqual(10.00, c.discount(10.00))
        #make sure it's indepent of price for dollar value coupons
        self.assertEqual(10.00, c.discount(25.00)) 
        
        c.is_percent = True
        self.assertEqual(2.5, c.discount(25.00)) 
        self.assertEqual(1.0, c.discount(10.00)) 

    def test_coupon_notification(self):     

        user = User()
        user.first_name = "justin"
        user.last_name = "gray"
        user.username = "justingray"
        user.email = "test@test.com"
        user.save()

        club = Club()
        club.name ="test-test"
        club.save()
 
        c = Coupon()
        c.discount_amount = "10.00"
        c.permanent = True
        c.code = "aaa"
        c.expires = datetime.date.today() + datetime.timedelta(days=1)
        c.club = club
        c.user_prof = user.get_profile()
        c.save()

        #make sure notification email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 
            u'New example.com coupon')
        
    def test_coupon_is_valid(self): 
        
        user = User()
        user.first_name = "justin"
        user.last_name = "gray"
        user.username = "justingray"
        user.email = "test@test.com"
        user.save()
        
        user2 = User()
        user2.first_name = "sirius"
        user2.last_name = "gray"
        user2.username = "tito"
        user2.save()

        club = Club()
        club.name ="test-test"
        club.save()
 
        c = Coupon()
        c.discount_amount = "10.00"
        c.permanent = True
        c.code = "aaa"
        c.expires = datetime.date.today() + datetime.timedelta(days=1)
        c.club = club
        c.save()
        
        o = Order()
        o.coupon = c
        o.user_prof = user.get_profile()
        o.save()
        
        self.assertTrue(c.is_valid(user))
        c.uses_left = 0
        self.assertTrue(c.is_valid(user))

        c.expires = datetime.date.today() - datetime.timedelta(days=1)    
        self.assertTrue(c.is_valid(user))

        c.permanent = False
        self.assertFalse(c.is_valid(user))

        c.expires = datetime.date.today() + datetime.timedelta(days=1)
        c.uses_left = 1
        self.assertTrue(c.is_valid(user))
        c.uses_left = 0
        self.assertFalse(c.is_valid(user))
        
        c.uses_left = 1
        c.user_prof = user.get_profile()
        self.assertFalse(c.is_valid(user2))
        
        c.user_prof = None
        c.single_use_per_user = True
        self.assertFalse(c.is_valid(user))
        

class TestOrder(unittest.TestCase): 
    
    def tearDown(self): 
        clear_db()
            
    def setUp(self): 
        self.c = Club()
        self.c.name = "test club"
        self.c.full_clean()
        self.c.save()
        
        self.season = Season()
        self.season.club = self.c
        self.season.year = 2011
        self.season.save()
        
        self.race_class = RaceClass()
        self.race_class.name = "CSP"
        self.race_class.pax = .875
        self.race_class.club = self.c
        self.race_class.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.season = self.season
        self.e.club = self.c
        self.e.save()        
        
        self.user = User()
        self.user.first_name = "justin"
        self.user.last_name = "gray"
        self.user.username = "justingray"
        self.user.save()
        
        self.user2 = User()
        self.user2.first_name = "sirius"
        self.user2.last_name = "gray"
        self.user2.username = "tito"
        self.user2.save()
    
    def test_total_price(self): 
        self.o = Order()
        self.o.user_prof = self.user.get_profile()
        self.o.save()        
        
        item1 = Registration()
        item1.number = 11
        item1.race_class = self.race_class
        item1.pax_class = None
        item1.event = self.e
        item1.price = "40.00"
        item1.order = self.o
        item1.club = self.c
        item1.save()
        
        item2 = Membership()
        item2.user_prof = self.user.get_profile()
        item2.club = self.c
        item2.num = 1
        item2.start = datetime.date.today() - datetime.timedelta(days=300)
        item2.valid_thru = datetime.date.today()+datetime.timedelta(days=1)
        item2.price = "60.00"
        item2.order = self.o
        item2.save()
        
        self.o.calc_total_price()
        self.assertEqual(self.o.total_price, "100.00")

        club = Club()
        club.name ="test-test"
        club.save()
        
        c = Coupon()
        c.discount_amount = "10.00"
        c.permanent = True
        c.code = "aaa"
        c.expires = datetime.date.today() + datetime.timedelta(days=1)
        c.club = club
        c.save()
        
        self.o.coupon = c
        self.o.calc_total_price()
        self.assertEqual(self.o.total_price, '90.00')        
