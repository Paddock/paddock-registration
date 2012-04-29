from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse


from django.contrib.auth.models import User
from paddock.models import Club


#django auth views
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

#paddodk forms
from forms import UserCreationForm, AuthenticationForm


def clubs(request):
    """club index page"""
    clubs = Club.objects.all()
    
    context = {'clubs':clubs,
               'club_count':len(clubs)}
    return render_to_response('paddock/clubs.html',
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
                        
            profile.send_activation_email()
            
            return HttpResponseRedirect(reverse('paddock.views.clubs'))
    else: 
        form = UserCreationForm() #unbound form (no data)   
        
    print "test", form.errors
        
    return render_to_response('paddock/registration_form.html',
                              {'form':form},
                              context_instance=RequestContext(request))

def activate(response): 
    pass