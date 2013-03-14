import StringIO
import datetime

from unittest import TestCase

from django.db import models as m
from django.contrib.auth.models import AnonymousUser

from garage.utils import parse_axtime

from registration.models import Session, Event, Club, Season, \
    RaceClass, User, Registration, Group, Permission

class TestParseAxtime(TestCase): 

    def setUp(self): 
        self.data = ['"First","Last","Reg","Class","Num","BC","Vehicle","Addr","City_St","Zip","Heat","Wrk_Ht","Wrk_Asgn","Notes","Mem_Num","Pax_Cls","Color","Sponsor","Tires","Co_Drvr","In_Pts","DL_Num","DL_St","DL_Exp","Fee","Pd_by","Run1_1","Pyl1_1","Pen1_1","Run2_1","Pyl2_1","Pen2_1","Run3_1","Pyl3_1","Pen3_1","Run4_1","Pyl4_1","Pen4_1","Run5_1","Pyl5_1","Pen5_1","Best_1","Run1_2","Pyl1_2","Pen1_2","Run2_2","Pyl2_2","Pen2_2","Run3_2","Pyl3_2","Pen3_2","Run4_2","Pyl4_2","Pen4_2","Run5_2","Pyl5_2","Pen5_2","Best_2","Pts_1","Pts_2","Pts_3","Pts_4","Pts_5","Pts_6","Pts_7","Pts_8","Pts_9","Pts_10","Pts_11","Pts_12","Pts_13","Pts_14","Pts_15","Pts_Bon","Indx_1","Indx_2","Indx_3","Indx_4","Indx_5","Indx_6","Indx_7","Indx_8","Indx_9","Indx_10","Indx_11","Indx_12","Indx_13","Indx_14","Indx_15","Indx_Bon"',
            '"CHRIS","BRUBAKER","NORA","STS","73","","97 MAZDA MIATA","","   ","     ","  1","  2","","22906","BRUBAKER","STS","","","","","Y","","  ","","   ","  ","  55.531"," 0","   ","  55.436"," 0","   ","  53.677"," 0","   ","  54.566"," 0","   ","   0.000"," 0","   ","  53.677","  53.873"," 0","   ","  54.056"," 0","   ","  53.792"," 0","   ","  53.803"," 0","   ","   0.000"," 0","   ","  53.792","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    "'
            ]

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
        self.e.save()

        self.session = Session()
        self.session.name = "am"
        self.session.club = self.c
        self.session.event = self.e
        self.session.save()

        self.rc = RaceClass()
        self.rc.name = "STS"
        self.rc.abrv = "STS"
        self.rc.pax = .95
        self.rc.club = self.c
        self.rc.save()

        self.rc2 = RaceClass()
        self.rc2.name = "Rookie"
        self.rc2.abrv = "R"
        self.rc2.pax = 1
        self.rc2.club = self.c
        self.rc2.pax_class = True
        self.rc2.save()

        self.rc3 = RaceClass()
        self.rc3.name = "STC"
        self.rc3.abrv = "STC"
        self.rc3.pax = .95
        self.rc3.club = self.c
        self.rc3.save()

    def tearDown(self): 

        models = [Registration,RaceClass,Club,Season,Event,Session,User]
        for model in models: 
            model.objects.all().delete()

    def test_missing_raceclass(self): 
        RaceClass.objects.all().delete()

        f = StringIO.StringIO("\n".join(self.data))

        results = parse_axtime(self.e,self.session,f)

        self.assertEqual(results,{'results_file': 'Your results for CHRIS BRUBAKER included an unknown race class: STS'})
        
    def test_with_raceclass_anon(self):
        f = StringIO.StringIO("\n".join(self.data))

        results = parse_axtime(self.e,self.session,f)
        
        result = results[0]
        runs = result.runs.all()

        self.assertEqual(len(runs),8)
        self.assertEqual(result.best_run,runs[2])

        self.assertEqual(result.reg._anon_f_name,'CHRIS')
        self.assertEqual(result.reg._anon_l_name,'BRUBAKER')
        self.assertEqual(result.reg.user, AnonymousUser())

    def test_with_raceclass(self):
        f = StringIO.StringIO("\n".join(self.data))

        user = User()
        user.first_name = "CHRIS"
        user.last_name = "brubaker"
        user.username = "brubaker"
        user.save()

        self.r = Registration()
        self.r.number = 11
        self.r.race_class = self.rc
        self.r.pax_class = None
        self.r.club = self.c
        self.r.event = self.e

        result = parse_axtime(self.e,self.session,f)[0]
        runs = result.runs.all()
        
        self.assertEqual(len(runs),8)
        self.assertEqual(result.best_run,runs[2])

        reg = result.reg
        self.assertEqual(reg.user,user)

        self.assertEqual(reg.number,73)

    def test_multi_results(self): 
        self.data.append('"CHRIS","MCPHERSON","NORA","R","13","","90 HONDA CIVIC SI","","   ","     ","  1","  2","","22929","SUMMERNIGH","STC","","","","","Y","","  ","","   ","  ","  59.740"," 0","   ","  58.399"," 0","   ","  56.798"," 2","   ","  57.131"," 0","   ","  55.374"," 0","   ","  55.374","  56.671"," 0","   ","  56.519"," 0","   ","  56.225"," 0","   ","  55.629"," 0","   ","   0.000"," 0","   ","  55.629","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    ","    "')
        f = StringIO.StringIO("\n".join(self.data))

        results = parse_axtime(self.e,self.session,f)

        self.assertEqual(len(results),2)

        result = results[0]
        self.assertEqual(result.reg.race_class,self.rc)
        self.assertEqual(result.reg.pax_class,None)

        result = results[1]
        self.assertEqual(result.reg.race_class,self.rc3)
        self.assertEqual(result.reg.pax_class,self.rc2)




