import datetime
from tastypie.test import ResourceTestCase

from registration.models import Registration, Event, RaceClass

class RegistrationResourceTest(ResourceTestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    fixtures = ['test_data.json',]

    def setUp(self):
        super(RegistrationResourceTest, self).setUp()

        
        # Fetch the ``Entry`` object we'll use in testing.
        # Note that we aren't using PKs because they can change depending
        # on what other tests are running.
        self.event = Event.objects.get(season__year='2011',safe_name="pointsevent13")
        self.rc = RaceClass.objects.get(club__safe_name="noraascc",abrv="CSP")
        regs = self.event.get_results()
        self.reg = regs[0]
        
        # We also build a detail URI, since we will be using it all over.
        # DRY, baby. DRY.
        self.list_url =   '/garage/api/v1/registration/'
        self.reg_detail_url = '/garage/api/v1/registration/{0}/'.format(self.reg.pk)
        self.event_url =  '/garage/api/v1/event/{0}/'.format(self.event.pk)
        self.rc_detail_url = '/garage/api/v1/raceclass/{0}/'.format(self.rc.pk)

        # The data we'll send on POST requests. Again, because we'll use it
        # frequently (enough).
        
        self.post_data = {'run_heat':None, 
                          'first_name':'justin', 
                          'last_name':'gray', 
                          'total_index_time':100.00, 
                          'checked_in':False, 
                          'work_heat':None, 
                          'index_points':1000, 
                          'number':11, 
                          'class_points':1000, 
                          'event':self.event_url, 
                          'car_name':'1990 mazda miata', 
                          'total_raw_time':100.00, 
                          'price':5.0, 
                          'user':'justingray', 
                          'race_class':self.rc_detail_url,
                         }
        
        
    def test_registration_json(self):
        resp = self.api_client.get(self.reg_detail_url, format='json')
        self.assertValidJSONResponse(resp)

        # We use ``assertKeys`` here to just verify the keys, not all the data.
        response = self.deserialize(resp)
        
        self.assertEqual(response['first_name'].strip(), 'Mike') 
        self.assertEqual(response['last_name'].strip(), 'Elsass') 
        
        resp = self.api_client.post(self.list_url, format='json',
                                    data=self.post_data)
        self.assertHttpCreated(resp)
        response = self.deserialize(resp)
                
    