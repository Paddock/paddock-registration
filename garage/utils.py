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
    