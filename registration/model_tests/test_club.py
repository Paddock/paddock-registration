from django.utils import unittest

from django.core.exceptions import ValidationError

from registration.models import Club


class TestClub(unittest.TestCase): 
    
    def tearDown(self): 
        Club.objects.all().delete()

    def testSafeName(self): 
        c = Club()
        c.name = "Some - Racers"

        c.save()
        self.assertEqual("someracers", c.safe_name)
        
        c.name = "some\\racers"
        c.save()
        self.assertEqual("someracers", c.safe_name)

    def testUniqueSafeName(self): 
        c = Club()
        c.name = "Some - Racers"

        c.save()

        new_c = Club()
        new_c.name = "some-racers"

        try: 
            new_c.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'safe_name': [u'Club with this Safe_name already exists.']}", str(err))
        else: 
            self.fail("ValidationError expected")
