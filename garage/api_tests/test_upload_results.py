from django.test import TestCase


class TestUploadResults(TestCase): 

    fixtures = ['test_data.json']

    def setUp(self): 
        self.c = Client()

    def test_upload_error(self):
    
        url = "/garage/event/61/results"    

