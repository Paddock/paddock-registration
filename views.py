from django.shortcuts import render_to_response

from paddock.models import Club

def clubs(request):

    clubs = Club.objects.all()
    
    context = {'clubs':clubs,
               'club_count':len(clubs)}
    return render_to_response('clubs.html',context)