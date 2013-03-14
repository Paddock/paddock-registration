import csv
import re

from registration.models import Result, RaceClass, UserProfile, User, Registration, Run

int_check = re.compile('^\d+$')

def reg_txt(regs): 
    """return a string with registration data formatted for axware"""

    lines = ""
    data = (("name",30),
            ("reg series",10),
            ("class",8),
            ("number",9),
            ("paid",4),
            ("member",8),
            #("work assignments",40))
            )
    line = "|".join([str(val).ljust(size) for val,size in data])
    count = len(line)
    lines = "".join([lines,line,'\r\n'])
    lines = "".join([lines,"="*count,'\r\n'])

    for reg in regs: 

        paid = "no" #TODO: need to fix this to work with purchasable
        if reg.paid: 
            paid = "yes"

        member = "no"
        if reg.user_profile and reg.user_profile.is_member(reg.event.season.club): 
            member = "yes"

        pax_class_name = ""
        if reg.pax_class: 
            pax_class_name = reg.pax_class.name    

        data = (
            ("%s, %s"%(reg.last_name,reg.first_name),30),
            (pax_class_name,10),
            (reg.race_class.name,8),
            (reg.number,9),
            (paid,4),
            (member,8),
            #(','.join([wp.name for wp in registration.work_prefs]),40)
        )  
        line = "|".join([str(val).ljust(size) for val,size in data])
        lines = "".join([lines,line,'\r\n'])
    return lines   

    

def reg_dat(regs):
    """return a string with registration data formatted for 
    human readable pre-reg sheet"""

    lines = ""
    for reg in regs: 
        if reg.pax_class: 
            reg_type_name = reg.pax_class.abrv
        else: 
            reg_type_name = reg.race_class.abrv
        club = reg.event.season.club    
        car_year = ""
        car_make = ""
        car_color = ""
        car_model = ""
        if reg.car: 
            car_year = str(reg.car.year)
            car_make = reg.car.make
            car_color = reg.car.color
            car_model = reg.car.model

        user_id=""
        if reg.user_profile: 
            user_id = reg.user_profile.user.pk

        data = ((reg_type_name,4),#1
                (reg.race_class.name,4),#2
                (reg.number,3),#3
                ("  Y",3), #run_heat 4
                ("  Y",3), #work_het 5
                ("",6), #bar_code 6
                (user_id,10), #member id number 7
                (club.name,5), #club_name 8
                ("Y",1), #in_points 9  
                (reg.first_name,15), #10
                (reg.last_name,15), #11
                ("",30), #address #12
                ("",15), #city #13
                ("",2), #state #14
                ("",5), #zip code #15
                (car_year[2:],2), #16
                (car_make,10), #17
                (car_model,10), #18
                (car_color,10), #19
                ("",30), #sponsor #20
                ("",10), #tires #21
                ("",20), #work_pref 22
                ("",3), # co-driver number 23
                (reg.id,30), #notes 24
                ("",15), #license number 25
                ("",2), #license st 26
                ("",2), #expires_month 27
                ("",2), #expires_day 27 
                ("",2), #expires_year 27
                ("",3), #entry_fee 28
                ("",2), #paid_by 29
        )    

        line_data = []
        for k,v in data:
            try:
                if k: line_data.append(str(k).ljust(v)[0:v].encode('ascii'))
                else: line_data.append("".ljust(v))
            except UnicodeError:
                k = k.encode('ascii','ignore')
                line_data.append(str(k.encode('ascii','ignore')).ljust(v)[0:v].encode('ascii'))
        line = "".join(line_data)
        lines ="".join([lines,line,'\r\n'])

    return lines

def parse_axtime(event,session,results_file): 
    """Expects a Session object and a file object with 
    and iterates through to return either a list of result instances, 
    or a dictionary containing error messages""" 

    validate_error = {}
    results = []  
    club = session.club

    reader = csv.reader(results_file)
    header = reader.next()
    header_check = ['First','Last','Reg','Class','Num','Vehicle',
                    'Pax_Cls','Color',"Notes","Heat"]
    if not all([h in header for h in header_check]):
        validate_error['results_file'] = "your file was missing some columns"
        return validate_error
    
    time_keys = [k for k in header if 'Run' in k]
    cone_keys = [k for k in header if 'Pyl' in k]
    pen_keys = [k for k in header if 'Pen' in k]
    
    if not all([time_keys,cone_keys,pen_keys]): 
        validate_error['result_file'] = "your file was missing some run results columns"
        return validate_error
        
    keys = header_check + time_keys + cone_keys + pen_keys
    for line in reader: 
        result = Result()
        result.session = session
        result.club = session.club

        data = dict(zip(header,line))
        reg_id = data['Notes']
        
        #find the group class and raceclass: 
        if data['Class']==data['Pax_Cls']: 
            group = None
        else: 
            try: 
                group = RaceClass.objects.get(abrv=data['Class'],club=club)
                       
            except RaceClass.DoesNotExist: 
                validate_error['result_file'] = 'Your Reults for %s %s included a unknown entry, %s in the Class column'%(data['First'],data['Last'],data['Class'])
                return validate_error
        
        try: 
            race_class = RaceClass.objects.get(abrv=data['Pax_Cls'],club=club)
        except RaceClass.DoesNotExist: 
            if not data['Pax_Cls']: 
                validate_error['results_file'] = "Your results for %s %s included an blank race class"%(data['First'],data['Last'])
            else: 
                validate_error['results_file'] = "Your results for %s %s included an unknown race class: %s"%(data['First'],data['Last'],data['Pax_Cls'])
            return validate_error

        car_data = data['Vehicle'].split()
        if len(car_data) == 3 and int_check.match(car_data[0]):
            data['Vehicle_year'] = car_data[0]
            data['Vehicle_make'] = car_data[1]
            data['Vehicle_model'] = car_data[2]
                
        elif len(car_data) == 2:
            data['Vehicle_year'] = None
            data['Vehicle_make'] = car_data[0]
            data['Vehicle_model'] = car_data[1]
        else:
            data['Vehicle_year'] = None
            data['Vehicle_make'] = None
            data['Vehicle_model'] = data['Vehicle'] 
                        
        #try REALLY hard to find the registration that maps to this driver
        try: 
            user = User.objects.filter(username__icontains=data['Mem_Num'], 
                first_name__icontains=data['First'], 
                last_name__icontains=data['Last'])[0]
        except IndexError: #coudn't find one
            user = None
           
        if user: 
            try:
                reg = Registration.objects.get(event=event,user_profile__user__username=user.username) 
                if reg.race_class != race_class:
                    reg.race_class = race_class
            
            except Registration.DoesNotExist:    
                reg = Registration()
                reg.user_profile = user.get_profile()
                reg.number = int(data['Num'])
                reg.race_class = race_class
                reg.pax_class = group
                reg._anon_car = data['Vehicle']
                reg.event = event
                reg.club = club
                reg.save()
            #not sure how this could happen at all...    
            #except Registration.MultipleObjectsReturned:
            #    reg = session.query(model.Registration).join(model.Driver).join(model.Event).\
            #            filter(model.Event.id==c.event.id).filter(model.Driver.user_name==driver.user_name).all()
            #    for r in reg: 
            #        session.delete(r)
            #    
            #    reg = model.Registration()
            #    reg.driver = driver
            #    reg.number = int(data['Num'])
            #    reg.race_class = race_class
            #    reg.anon_car = unicode(data['Vehicle'])
            #    reg.event = c.event
                
        else:  
            #try to find a previous anon_reg
            try:
                reg = Registration.objects.get(event=event, _anon_f_name=data['First'], 
                    _anon_l_name=data['Last'])        
                        
            except Registration.DoesNotExist: 
                reg = Registration()
                reg.number = int(data['Num'])
                reg.race_class = race_class
                reg.pax_class = group
                
                reg._anon_f_name = data['First']
                reg._anon_l_name = data['Last']
                reg._anon_car = data['Vehicle']
                reg.event = event
                reg.club = club
                reg.save()
            
        try: 
            reg.number = int(data['Num']) 
        except Exception,err: 
             validate_error['results_file'] = 'Problem with car number for entry: %s %s'%(reg.first_name,reg.last_name)
             return validate_error

        result.reg = reg 
        result.save()

        for r_key,c_key,p_key in zip(time_keys,cone_keys,pen_keys):
            run = Run()
            run.result = result
            run.club = club
            try: 
                if float(data[r_key]) <= 0.0: continue
            except ValueError: 
                continue

            run.base_time = float(data[r_key])
            run.cones = int(data[c_key])
            if data[p_key].strip():
                run.penalty = data[p_key]
            run.save()
        reg.save()
        results.append(result)

    return results
               
    