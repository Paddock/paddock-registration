"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""


from django.test import TestCase
from django.contrib.auth.models import User

from django.test.client import Client

from django.db import models as m

from django.contrib.auth import authenticate, login


from tastypie.test import ResourceTestCase

#from garage.api_tests.test_api import RegistrationResourceTest

from registration.models import Club, Group, Permission, User


class TestPermissions(TestCase): 

    def setUp(self): 
        self.c = Club()
        self.c.name = "test"
        self.c.save()

    def tearDown(self):
        for model in m.get_models(): 
            model.objects.all().delete()      

    def test_group_created(self): 
        try: 
            g = Group.objects.get(name="test_admin")
        except Group.DoesNotExist as err: 
            self.fail('club admin group not created')

    def test_permissions(self): 
    
        user = User()
        user.first_name = "Justin"
        user.last_name = "Gray"
        user.username = "justingray"
        user.save()
        
        self.c.group.user_set.add(user)

        self.assertTrue(user.has_perm('registration.test_admin'))



class TestAPIPermissions(ResourceTestCase): 

    def setUp(self): 
        super(TestAPIPermissions, self).setUp()

        self.c = Club()
        self.c.name = "test"
        self.c.save()

        self.user = User()
        self.user.first_name = "Justin"
        self.user.last_name = "Gray"
        self.user.username = "justingray"
        self.user.save()

        self.user.set_password("test")
        self.user.save()

        self.c.group.user_set.add(self.user)

        self.user2 = User()
        self.user2.first_name = "Eli"
        self.user2.last_name = "Gray"
        self.user2.username = "eligray"
        self.user2.save()

        self.user2.set_password("test")
        self.user2.save()

        self.detail_url = '/garage/api/v1/club/{0}/'.format(self.c.pk) 
        self.list_url = '/garage/api/v1/club/' 

    def tearDown(self):
        for model in m.get_models(): 
            model.objects.all().delete()   

    def get_credentials(self):
        resp = self.api_client.client.login(username='justingray',
                                              password='test')
        return resp

    def test_not_allowed(self): 
        resp = self.api_client.get(self.detail_url, format="json", 
            authenticate=self.get_credentials())
        self.assertHttpUnauthorized(resp)



    def test_list_club_admins(self): 
        self.client.login(username='justingray', password='test')   

        resp = self.api_client.get(self.detail_url, format="json", 
            authenticate=self.get_credentials())

        self.assertValidJSONResponse(resp)
        data = self.deserialize(resp)
        self.assertEqual([{u'username': u'justingray', u'first_name': u'Justin', u'last_name': u'Gray', u'email': u''}], 
            data['admins'])

        new_data = data.copy()
        new_data['admins'].append({u'username': u'eligray'})
        #use2 should not have permissions yet
        self.assertFalse(self.user2.has_perm('registration.test_admin'))
        resp = self.api_client.post(self.list_url, format='json', data=new_data, 
            authentication=self.get_credentials())
        self.assertHttpCreated(resp)

        #make sure the new person was added to the list
        resp = self.api_client.get(self.detail_url, format="json", 
            authenticate=self.get_credentials())
        self.assertValidJSONResponse(resp)
        data = self.deserialize(resp)
        self.assertEqual([{u'username': u'justingray', u'first_name': u'Justin', u'last_name': u'Gray', u'email': u''},
            {u'username': u'eligray', u'first_name': u'Eli', u'last_name': u'Gray', u'email': u''}], 
            data['admins'])

        #justin should still have perms
        u = User.objects.get(username='justingray') 
        #mser2 should now have permissions
        self.assertTrue(u.has_perm('registration.test_admin'))

        u = User.objects.get(username='eligray') #need to re-get from db here, for perms to update
        #eli should now has permissions
        self.assertTrue(u.has_perm('registration.test_admin'))

        #try empty admins list
        new_data['admins'] = []
        resp = self.api_client.post(self.list_url, format='json', data=new_data, 
            authentication=self.get_credentials())
        self.assertHttpCreated(resp)
        
