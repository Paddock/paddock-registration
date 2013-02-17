import datetime

import django.test
from django.utils import unittest
from django.core.exceptions import ValidationError
from django.db import models as m


from registration.models import Event, Registration, Season, Club, Session, Result, \
     Run, RaceClass, User

from registration.points_calculators.nora_index_points import point_ladder as index_point_ladder
from registration.points_calculators.nora_class_points import point_ladder as class_point_ladder


class TestEvent(unittest.TestCase): 
    
    def setUp(self): 
        self.c = Club()
        self.c.name = "test"
        self.c.save()
        
        self.s = Season()
        self.s.year = 2011
        self.s.club = self.c
        self.s.save()
        
        self.e = Event()
        self.e.name = "test event"
        self.e.date = datetime.date.today()
        self.e.season = self.s
        self.e.club = self.c
        
    def tearDown(self): 
        
        for model in m.get_models(): 
            model.objects.all().delete()        
        
    def testEventSafeName(self): 
        pass
    
    def testEventisRegd(self): 
        
        self.e.save()
        
        u = User()
        u.first_name = "Justin" 
        u.last_name = "Gray"
        u.username = "JustinGray"
        
        u.save()
        
        rc = RaceClass()
        rc.abrv = "CSP"
        rc.name = "CSP"
        rc.pax = 1
        rc.club = self.c
        rc.save()
                
        self.assertFalse(self.e.is_regd(u))        
        
        r = Registration()
        r.event = self.e
        r.number = 11
        r.race_class = rc
        r.user_profile = u.get_profile()
        r.club = self.c
        r.save()
        
        self.assertTrue(self.e.is_regd(u))
    
    def testValidRegClose(self): 
        
        try: 
            self.e.reg_close = datetime.datetime.today()+datetime.timedelta(days=1)
            self.e.full_clean()
        except ValidationError as err: 
            self.assertEqual("{'__all__': [u'Registration must close before the date of the event.']}", str(err))
        else: 
            self.fail("ValidationError expected")     
                
    def test_event_reg_limit(self): 
        self.e.save()
        self.sess = Session()
        self.sess.name = "AM"
        self.sess.event = self.e
        self.sess.club = self.c
        self.sess.save()
                
        self.race_class = RaceClass()
        self.race_class.name = "A"
        self.race_class.pax = 1
        self.race_class.club = self.c
        self.race_class.save()        
        
        self.e.reg_limit = 3
        self.e.save()
        
        for i in range(0, 4): 
            try: 
                self.r = Registration()
                self.r.number = i
                self.r.race_class = self.race_class
                self.r._anon_f_name = "random_%d"%(i,)
                self.r.pax_class = None
                self.r.event = self.e
                self.r.club = self.c
                self.r.save()
                
            except ValidationError as err: #don't error untill the limit is reached  
                self.assertEqual(i, 3)
            else: 
                self.assertLess(i, 3)
        
    
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
        self.e.club = self.c
        self.e.save()
        
        self.sess = Session()
        self.sess.name = "AM"
        self.sess.event = self.e
        self.sess.club = self.c
        self.sess.save()
        
        self.classes = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self.paxes   = [1.0, .98, .96, .94, .92, .90, .88, .86]
        for klass, pax in zip(self.classes, self.paxes): 
            self.race_class = RaceClass()
            self.race_class.name = klass
            self.race_class.pax = pax
            self.race_class.club = self.c
            self.race_class.save()
            
            for i in range(0, 10): 
                self.r = Registration()
                self.r.number = i
                self.r.race_class = self.race_class
                self.r._anon_f_name = "%s%d"%(self.race_class.name, i)
                self.r.pax_class = None
                self.r.event = self.e
                self.r.club = self.c
                self.r.save()
                
                #make two regs with empty runs for each class
                if self.race_class.name!="H" and i < 8: #one race class with no results
                    self.result = Result()
                    self.result.reg = self.r
                    self.result.session = self.sess
                    self.result.club = self.c
                    self.result.save()
                    for j in range(0, 3): 
                        run = Run()
                        run.base_time = 100.0-i-j #91.0 is lowest raw time (*0.88 for index)
                        run.result = self.result
                        run.club = self.c
                        run.save()        
                            
    def tearDown(self): 
        for model in m.get_models(): 
            model.objects.all().delete()

    def test_no_index_classes_one_result(self): 
        
        race_classes = self.e.calc_results()
        self.assertEqual(["A", "B", "C", "D", "E", "F", "G"], [rc.name for rc in race_classes])
                
        #make sure the results come back sorted
        for rc, regs in race_classes.iteritems(): #all race_classes should have 8 regs in the results    
            self.assertEqual(regs, sorted(regs, key=lambda x: x.total_index_time))

            self.assertEqual(class_point_ladder[:8], [reg.class_points for reg in regs])
            
            self.assertEqual(8, len(regs))
            
        regs = self.e.get_results()
        self.assertEqual(regs[0].total_index_time, (91.0)*.88)
        self.assertEqual(index_point_ladder[:56], [reg.index_points for reg in regs])
        
    def test_no_index_classes_two_result(self): 
        
        self.sess = Session()
        self.sess.name = "PM"
        self.sess.event = self.e
        self.sess.club = self.c
        self.sess.save()

        for klass, pax in zip(self.classes, self.paxes): 
            self.race_class = RaceClass.objects.filter(name=klass).get()            
            for i in range(0, 10): 
                self.r = Registration.objects.filter(_anon_f_name="%s%d"%(self.race_class.name, i)).get()
                
                #make  regs with empty runs for each class
                if self.race_class.name!="H" and i < 8: #one race class with no results
                    self.result = Result()
                    self.result.reg = self.r
                    self.result.session = self.sess
                    self.result.club = self.c
                    self.result.save()
                    for j in range(0, 3): 
                        run = Run()
                        run.base_time = 100.0-i-j
                        run.result = self.result
                        run.club = self.c
                        run.save()   
                self.r = Registration.objects.filter(_anon_f_name="%s%d"%(self.race_class.name, i)).get()        
                
        race_classes = self.e.calc_results()
        self.assertEqual(["A", "B", "C", "D", "E", "F", "G"], [rc.name for rc in race_classes])
                
        #make sure the results come back sorted
        for rc, regs in race_classes.iteritems(): #all race_classes should have 8 regs in the results    
            self.assertEqual(regs, sorted(regs, key=lambda x: x.total_index_time))

            self.assertEqual(class_point_ladder[:8], [reg.class_points for reg in regs])
            
            self.assertEqual(8, len(regs))
            
        regs = self.e.get_results()
        self.assertEqual(regs[0].total_index_time, 2*(91.0)*.88)
        self.assertEqual(index_point_ladder[:56], [reg.index_points for reg in regs])
        
    def test_pax_class_one_result(self): 
        
        self.race_class = RaceClass()
        self.race_class.name = "Pro"
        self.race_class.abrv ="X"
        self.race_class.pax = 1.0
        self.race_class.pax_class=True
        self.race_class.club = self.c
        self.race_class.save()

        for i, pax_name in zip(range(0, 7), self.classes): 
            
            rc = RaceClass.objects.filter(name=pax_name).get()
            
            self.r = Registration()
            self.r.number = 10*(1+i)
            self.r.race_class = rc
            self.r._anon_f_name = "%s_%d"%(self.race_class.name, i)
            self.r.pax_class = self.race_class
            self.r.event = self.e
            self.r.club = self.c
            self.r.save()
            
            #make  regs with runs for each class
            if rc.name!="H": 
                self.result = Result()
                self.result.reg = self.r
                self.result.session = self.sess
                self.result.club = self.c
                self.result.save()
                for j in range(0, 3): 
                    run = Run()
                    run.base_time = 100.0-i-j
                    run.result = self.result
                    run.club = self.c
                    run.save()   
                
        race_classes = self.e.calc_results()
        self.assertEqual([u"A", u"B", u"C", u"D", u"E", u"F", u"G", u"Pro"], [rc.name for rc in race_classes])
                
        #make sure the results come back sorted
        for rc, regs in race_classes.iteritems(): #all race_classes should have 8 regs in the results    
            self.assertEqual(regs, sorted(regs, key=lambda x: x.total_index_time))

            if rc.name != "Pro": 
                self.assertEqual(class_point_ladder[:8], [reg.class_points for reg in regs])
                self.assertEqual(8, len(regs))
            else: 
                self.assertEqual(class_point_ladder[:7], [reg.class_points for reg in regs])
                self.assertEqual(7, len(regs))
                
        regs = self.e.get_results()
        self.assertEqual(regs[0].total_index_time, (91.0)*.88)
        self.assertEqual(index_point_ladder[:63], [reg.index_points for reg in regs])  
        
    def test_one_bump_class_one_result(self): 
        
        self.race_class = RaceClass()
        self.race_class.name = "index"
        self.race_class.pax = 1.0
        self.race_class.club = self.c
        self.race_class.save()

        for i, pax_name in zip(range(0, 7), self.classes): 
            
            rc = RaceClass.objects.filter(name=pax_name).get()
            
            self.r = Registration()
            self.r.number = 10*(1+i)
            self.r.race_class = rc
            self.r._anon_f_name = "%s_%d"%(self.race_class.name, i)
            self.r.bump_class = self.race_class
            self.r.event = self.e
            self.r.club = self.c
            self.r.save()
            
            #make  regs with empty runs for each class
            if rc.name!="H": 
                self.result = Result()
                self.result.reg = self.r
                self.result.session = self.sess
                self.result.club = self.c
                self.result.save()
                for j in range(0, 3): 
                    run = Run()
                    run.base_time = 100.0-i-j
                    run.result = self.result
                    run.club = self.c
                    run.save()   
                
        race_classes = self.e.calc_results()
        self.assertEqual(["A", "B", "C", "D", "E", "F", "G", "index"], [rc.name for rc in race_classes])
                
        #make sure the results come back sorted
        for rc, regs in race_classes.iteritems(): #all race_classes should have 8 regs in the results    
            self.assertEqual(regs, sorted(regs, key=lambda x: x.total_index_time))

            if rc.name != "index": 
                self.assertEqual(class_point_ladder[:8], [reg.class_points for reg in regs])
                self.assertEqual(8, len(regs))
            else: 
                self.assertEqual(class_point_ladder[:7], [reg.class_points for reg in regs])
                self.assertEqual(7, len(regs))
            
        regs = self.e.get_results()
        self.assertEqual(regs[0].total_index_time, (91.0)*.88)
        self.assertEqual(index_point_ladder[:63], [reg.index_points for reg in regs])  
        
    def test_two_bump_class_one_result(self): 
        
        self.race_class1 = RaceClass()
        self.race_class1.name = "index1"
        self.race_class1.pax = 1.0
        self.race_class1.club = self.c
        self.race_class1.save()
        
        self.race_class2 = RaceClass()
        self.race_class2.name = "index2"
        self.race_class2.pax = 1.0
        self.race_class2.club = self.c
        self.race_class2.save()

        for i, pax_name in zip(range(0, 7), self.classes): 
            
            pax_class = RaceClass.objects.filter(name=pax_name).get()
            
            self.r = Registration()
            self.r.number = 10*(1+i)
            self.r.race_class = pax_class
            self.r._anon_f_name = "%s_%d"%(self.race_class2.name, i)
            self.r.bump_class = self.race_class1
            self.r.event = self.e
            self.r.club = self.c
            self.r.save()
            
            #make  regs with empty runs for each class
            if pax_class.name!="H": 
                self.result = Result()
                self.result.reg = self.r
                self.result.session = self.sess
                self.result.club = self.c
                self.result.save()
                for j in range(0, 3): 
                    run = Run()
                    run.base_time = 100.0-i-j
                    run.result = self.result
                    run.club = self.c
                    run.save()  
                    
                self.r = Registration()
                self.r.number = 60*(1+i)
                self.r.race_class = pax_class
                self.r._anon_f_name = "%s_%d"%(self.race_class2.name, i)
                self.r.bump_class = self.race_class2
                self.r.event = self.e
                self.r.club = self.c
                self.r.save()
                
                #make  regs with empty runs for each class
                if pax_class.name!="H": 
                    self.result = Result()
                    self.result.reg = self.r
                    self.result.session = self.sess
                    self.result.club = self.c
                    self.result.save()
                    for j in range(0, 3): 
                        run = Run()
                        run.base_time = 100.0-i-j
                        run.result = self.result
                        run.club = self.c
                        run.save()               
                    
        race_classes = self.e.calc_results()
        self.assertEqual(set(["A", "B", "C", "D", "E", "F", "G", "index1", "index2"]), set([rc.name for rc in race_classes]))
                
        #make sure the results come back sorted
        for rc, regs in race_classes.iteritems(): #all race_classes should have 8 regs in the results    
            self.assertEqual(regs, sorted(regs, key=lambda x: x.total_index_time))

            if "index" not in rc.name: 
                self.assertEqual(class_point_ladder[:8], [reg.class_points for reg in regs])
                self.assertEqual(8, len(regs))
            else: 
                self.assertEqual(class_point_ladder[:7], [reg.class_points for reg in regs])
                self.assertEqual(7, len(regs))
                
        regs = self.e.get_results()
        self.assertEqual(regs[0].total_index_time, (91.0)*.88)
        self.assertEqual(index_point_ladder[:70], [reg.index_points for reg in regs])      
        
        