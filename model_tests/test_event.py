import datetime

from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m

from paddock.models import Event, Registration, Season, Club, Session, Result, Run, RaceClass

from paddock.points_calculators.nora_index_points import point_ladder as index_point_ladder
from paddock.points_calculators.nora_class_points import point_ladder as class_point_ladder

class TestEvent(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test"
        
        self.s = Season()
        self.s.year = 2011
        self.s.club = self.c
        self.s.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.season = self.s
        
    def tearDown(self): 
        self.s.delete()
        
    def testEventSafeName(self): 
        pass
    
    def testValidRegClose(self): 
        
        try: 
            self.e.reg_close = datetime.datetime.today()+datetime.timedelta(days=1)
            self.e.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'Registration must close before the date of the event.']}",str(err))
        else: 
            self.fail("ValidationError expected")
            
            
class TestEventPointsCalc(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test club"
        self.c.full_clean()
        self.c.save()
        
        self.season = Season()
        self.season.club = self.c
        self.season.year = 2011
        self.season.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.season = self.season
        self.e.save()
        
        self.sess = Session()
        self.sess.name = "AM"
        self.sess.event = self.e
        self.sess.save()
        
        classes = ["A","B","C","D","E","F","G","H"]
        paxes   = [1.0,.98,.96,.94,.92,.90,.88,.86]
        for klass,pax in zip(classes,paxes): 
            self.race_class = RaceClass()
            self.race_class.name = klass
            self.race_class.pax = pax
            self.race_class.club = self.c
            self.race_class.save()
            
            for i in range(0,10): 
                self.r = Registration()
                self.r.number = 0
                self.r.race_class = self.race_class
                self.r._anon_f_name = "%d"%i
                self.r.pax_class = None
                self.r.event = self.e
                self.r.save()
                
                #make two regs with empty runs for each class
                if self.race_class.name!="H" and i < 8: #one race class with no results
                    self.result = Result()
                    self.result.reg = self.r
                    self.result.session = self.sess
                    self.result.save()
                    for j in range(0,3): 
                        run = Run()
                        run.base_time = 100.0-i-j
                        run.result = self.result
                        run.save()        
                            
                       
    
    def tearDown(self): 
        for model in m.get_models(): 
            model.objects.all().delete()
            
    def test_no_index_classes_one_result(self): 
        
        race_classes = self.e.calc_results()
        self.assertEqual(["A","B","C","D","E","F","G"],[rc.name for rc in race_classes])
        
        rc_A = RaceClass.objects.filter(name="A").get()
        
        #make sure the results come back sorted
        for rc,regs in race_classes.iteritems(): #all race_classes should have 8 regs in the results    
            self.assertEqual(regs, sorted(regs,key=lambda x: x.total_index_time))

            self.assertEqual(class_point_ladder[:8],[reg.class_points for reg in regs])
            
            self.assertEqual(8, len(regs))
            
        regs = self.e.get_results()
        self.assertEqual(index_point_ladder[:56],[reg.index_points for reg in regs])
        
        
            
            
            
        
      
        
        