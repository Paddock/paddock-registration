point_ladder = [20,17,14,12,10,8,6,4,2,1]

def calc_points(place,first_place_time,time): 
    
    if place > 10: 
        return 0
    else: 
        return point_ladder[place-1]
        
    
    