import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError

from paddock.models import Coupon

class TestCoupon(unittest.TestCase): 
    
    def setUp(self):
        self.c = Coupon()
    
    def tearDown(self): 
        pass
    
    def test_validcode(self): 
        
        self.c.code = "test code"
        
        try: 
            self.c.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'code': [u'Spaces not allowed in the code']}",str(err))
        else: 
            self.fail("ValidationError expected")
            
    def test_expires(self):  
        self.c.expires = datetime.date.today()
        self.c.code = "testcode"
        try: 
            self.c.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'expires': [u'Date must be at least one day from now']}",str(err))
        else: 
            self.fail("ValidationError expected")