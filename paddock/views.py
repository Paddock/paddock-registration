from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site

from paddock.models import Club,Event,Season

#django auth views
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

#paddodk forms
from forms import UserCreationForm, AuthenticationForm, ActivationForm


def clubs(request):
    """club index page"""
    clubs = Club.objects.all()
        
    context = {'clubs':clubs}

    return render_to_response('paddock/clubs.html',
                              context,
                              context_instance=RequestContext(request))

def event(request,club_name,season_year,event_name): 
    """single event page""" 
    
    event = Event.objects.get(season__club__safe_name=club_name,
                              season__year=season_year,
                              safe_name=event_name)
    context = {'event': event,
               'season': event.season, 
               'club': event.season.club}
    
    return render_to_response('paddock/event.html',
                              context,
                              context_instance=RequestContext(request))
    

def register(request): 
    """handles redering of new user form and creation of users"""
    
    #TODO: redirect somewhere else if authenticated user
    
    if request.method == 'POST': # If the form has been submitted...
        form = UserCreationForm(request.POST) #bound for, with submitted data
        
        if form.is_valid(): 
            #then create the user from the form data
            u = User.objects.create_user(form.cleaned_data['username'], 
                                         password=form.cleaned_data['password1'])
            u.is_active = False #only active after email verification
            
            u.save()
            
            profile = u.get_profile()
                        
            profile.send_activation_email(request)
            
            return HttpResponseRedirect(reverse('paddock.views.activate'))
    else: 
        form = UserCreationForm() #unbound form (no data)   
        
        
    return render_to_response('paddock/registration_form.html',
                              {'form':form},
                              context_instance=RequestContext(request))

def activate(request): 
    set_valid = False
    form = ActivationForm()
    if request.method == 'POST': #form submission
        form = ActivationForm(request.POST) #bound form            
        if form.is_valid(): 
            set_valid = True
       
    #link from email
    elif request.GET.get('username') and request.GET.get('activation_key'): 
        form = ActivationForm(initial={'username': request.GET.get('username'),
                                       'activation_key':request.GET.get('activation_key')})        
        if form.is_valid():
            set_valid = True
            
    if set_valid: 
        u = User.objects.get(username=form.cleaned_data['username'])
        u.is_active = True
        u.save()
        return HttpResponseRedirect(reverse('paddock.views.login')) 
        
    return render_to_response('paddock/activate_form.html',
                              {'form':form},
                              context_instance=RequestContext(request))