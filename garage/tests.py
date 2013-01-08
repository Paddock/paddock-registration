"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""


from django.test import TestCase
from django.contrib.auth.models import User

from django.test.client import Client

#from garage.api_tests.test_api import RegistrationResourceTest


class TestViews(TestCase): 
    fixtures = ['test_data.json']
    
    def setUp(self): 
        self.c = Client()
        
    def test_index_views(self):
        urls = [
                 ('/garage/users/justingray/',{}),
               ]
        
        for addr, args in urls: 
            response = self.c.get(addr, args)
            self.assertEqual(response.status_code, 200)

