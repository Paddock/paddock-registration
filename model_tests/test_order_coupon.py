import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m

from paddock.models import Registration, User, UserProfile, RaceClass, Event, Club, RegDetail,\
     Coupon, Order

class TestCoupon(unittest.TestCase):   
    
    def tearDown(self): 
        for model in m.get_models(): 
            model.objects.all().delete()
    
    def test_discount_calculation(self): 
        c = Coupon()
        c.discount_amount = "10.00"
        
        self.assertEqual(10.00, c.discount(10.00))
        #make sure it's indepent of price for dollar value coupons
        self.assertEqual(10.00, c.discount(25.00)) 
        
        c.is_percent = True
        self.assertEqual(2.5, c.discount(25.00)) 
        self.assertEqual(1.0, c.discount(10.00)) 
        
    def test_coupon_is_valid(self): 
        
        user = User()
        user.first_name = "justin"
        user.last_name = "gray"
        user.username = "justingray"
        user.save()
        
        user2 = User()
        user2.first_name = "sirius"
        user2.last_name = "gray"
        user2.username = "tito"
        user2.save()
        
        up = UserProfile()
        up.user = user
        up.save()
        
        up2 = UserProfile()
        up2.user = user2
        up2.save()
        
        
        c = Coupon()
        c.discount_amount = "10.00"
        c.permanent = True
        c.code = "aaa"
        c.expires = datetime.date.today() + datetime.timedelta(days=1)
        c.save()
        
        o = Order()
        o.coupon = c
        o.user_prof = up
        o.save()
        
        self.assertTrue(c.is_valid(user))
        c.uses_left = 0
        self.assertTrue(c.is_valid(user))

        c.expires = datetime.date.today() - datetime.timedelta(days=1)        
        self.assertFalse(c.is_valid(user))
        
        c.expires = datetime.date.today() + datetime.timedelta(days=1)
        c.permanent = False
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        