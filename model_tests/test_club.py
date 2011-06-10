from django.utils import unittest

from django.core.exceptions import ValidationError

from paddock.models import Club

class TestClub(unittest.TestCase): 

    def testSafeName(self): 
        c = Club()
        c.name = "Some - Racers"

        c.full_clean()
        self.assertEqual("some-racers", c.safe_name)

        c = Club()
        c.name = "some\\racers"
        self.assertEqual("some%5cracers", c.safe_name)

    def testUniqueSafeName(self): 
        c = Club()
        c.name = "Some - Racers"

        c.save()

        new_c = Club()
        new_c.name = "some-racers"

        try: 
            new_c.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'safe_name': [u'Club with this Safe_name already exists.']}",str(err))









