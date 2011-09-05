import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m

from paddock.models import Registration, User, RaceClass, Event, Club, RegDetail,\
     Coupon, Order

class TestCoupon(unittest.TestCase):     
    
    def test_discount_calculation(self): 
        c = Coupon()
        c.discount_amount = "10.00"
        
        self.assertEqual(10.00, c.discount(10.00))
        #make sure it's indepent of price for dollar value coupons
        self.assertEqual(10.00, c.discount(25.00)) 
        
        c.is_percent = True
        self.assertEqual(2.5, c.discount(25.00)) 
        self.assertEqual(1.0, c.discount(10.00)) 
        
        
        