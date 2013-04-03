from collections import OrderedDict
import json

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core import serializers
#from django.views.generic.create_update import create_object, update_object

from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login, logout, password_reset
from django.contrib.auth.decorators import login_required

from django.forms import ModelChoiceField, HiddenInput

from paypal.standard.forms import PayPalPaymentsForm

from registration.models import Club, Event, Car, UserProfile, Order

from registration.forms import (UserCreationForm, ActivationForm, 
    RegForm, CarAvatarForm, form_is_for_self, AuthenticationForm, 
    CarChoiceField
    )


JSON = serializers.get_serializer('json')
toJSON = JSON() #need an instance of the serializer


def login(request, *args, **kwargs):
    if request.method == 'POST':
        if not request.POST.get('remember_me', None): 
            request.session.set_expiry(0)    

    kwargs.update({'template_name': 'registration/login.html',
                   'authentication_form': AuthenticationForm})
               
    return django_login(request, *args, **kwargs)


def clubs(request):
    """club index page"""
    clubs = Club.objects.all()
        
    context = {'clubs': clubs}

    return render_to_response('registration/clubs.html',
                              context,
                              context_instance=RequestContext(request))


def event(request, club_name, season_year, event_name): 
    """single event page""" 
    
    event = Event.objects.select_related('regs', 'season').\
        get(season__club__safe_name=club_name,
            season__year=season_year,
            safe_name=event_name)
    
    reg_is_open = event.reg_is_open

    if reg_is_open: 
        regs = event.regs.all()
    else: 
        regs = event.get_results()

    reg_sets = {}
    
    for r in regs: 
        if r.pax_class: 
            reg_sets.setdefault(r.pax_class, []).append(r) 
        elif r.bump_class: 
            reg_sets.setdefault(r.bump_class, []).append(r)
        else: 
            if reg_is_open: 
                reg_sets.setdefault(None, []).append(r)
            else: 
                reg_sets.setdefault(None, {}).setdefault(r.race_class, []).append(r)
    
    reg_sets = OrderedDict(sorted(reg_sets.items(), key=lambda t: t[0], reverse=True))  

    is_regd = False
    is_auth = request.user.is_authenticated()
    if is_auth: 
        is_regd = event.is_regd(request.user)
        
    context = {'event': event,
               'season': event.season, 
               'club': event.season.club, 
               'regs': regs,
               'reg_sets': reg_sets,
               'reg_count': regs.count(),
               'reg_is_open': reg_is_open,
               'is_regd': is_regd,
               'is_auth': is_auth}
    
    if reg_is_open: 
        return render_to_response('registration/upcoming_event.html',
                                  context,
                                  context_instance=RequestContext(request))
    else: 
        context['index_points'], context['class_points'] = event.season.points_as_of(event.date) 
        context['top_pax_reg'] = regs[0]
        context['top_raw_reg'] = regs.order_by('-n_runs', 'total_raw_time')[0]        
        return render_to_response('registration/complete_event.html',
                                  context,
                                  context_instance=RequestContext(request)) 
    

@login_required
@form_is_for_self(RegForm, 'user_profile')
def event_register(request, club_name, season_year, event_name, username=None): 
    """register for an event""" 
    up = request.user.get_profile()
    e = Event.objects.select_related('season', 'season__club', 'user_profile').\
        get(season__club__safe_name=club_name,
            season__year=season_year,
            safe_name=event_name)    
    redirect_target = reverse('registration.views.event', args=[club_name, season_year, event_name])
    form_template = 'registration/event_reg_form.html'
    
    class UserRegForm(RegForm): #have to create the form here, since it's specific to a user
        car = CarChoiceField(queryset=Car.objects.filter(user_profile=up))
        event = ModelChoiceField(queryset=Event.objects.filter(pk=e.pk),
                                 initial=e.pk, widget=HiddenInput())
        club = ModelChoiceField(queryset=Club.objects.filter(pk=e.club.pk), 
                                initial=e.club.pk, widget=HiddenInput())
        user_profile = ModelChoiceField(queryset=UserProfile.objects.filter(pk=up.pk),
                                        initial=up.pk, widget=HiddenInput())

    reg = None
    if username: 
        reg = e.regs.get(user_profile__user__username=username)

    if request.method == 'POST':
        form = UserRegForm(request.POST, request.FILES, 
            user=request.user, instance=reg)
        if form.is_valid():
            reg = form.save()
            if form.cleaned_data['prepay']: 
                #figure out base reg price (member or not?)
                member = up.is_member(e.club)
                if member: 
                    reg.price = e.member_price
                else: 
                    reg.price = e.non_member_price

                up = request.user.get_profile()
                #construct order, add reg to order
                order = Order()
                order.user_prof = up
                order.coupon = form.coupon
                order.save()
                reg.order = order
                reg.save()

                # What you want the button to do.
                paypal_dict = {
                    "business": e.club.paypal_email,
                    "amount": order.calc_total_price(),
                    "item_name": 'Registration for %s %s'%(e.club.name, e.name),
                    "invoice": order.pk,
                    "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
                    "return_url": request.build_absolute_uri(redirect_target),
                    "cancel_return": request.build_absolute_uri(redirect_target),

                }
                paypal_form = PayPalPaymentsForm(initial=paypal_dict)

                context={
                    'paypal_form': paypal_form,
                    'price': paypal_dict['amount'],
                    'club': e.club, 
                    'order': order
                }
                
                return render_to_response('registration/start_pay.html',
                                          context,
                                          context_instance=RequestContext(request))

            return HttpResponseRedirect(redirect_target)
    else:
        form = UserRegForm(instance=reg)

    context={
        'event': e,
        'season': e.season,
        'club':  e.club,
        'form': form, 
    } 
    return render_to_response(form_template,
                              context,
                              context_instance=RequestContext(request))                               


#new user registration
def register(request): 
    """handles redering of new user form and creation of users"""
    
    #TODO: redirect somewhere else if authenticated user
    
    if request.method == 'POST': # If the form has been submitted...
        form = UserCreationForm(request.POST) #bound for, with submitted data
        
        if form.is_valid(): 
            #then create the user from the form data
            u = User.objects.create_user(username=form.cleaned_data['username'], 
                                         password=form.cleaned_data['password1'], 
                                         email=form.cleaned_data['email'])
            #u = form.save()
            u.is_active = False #only active after email verification
            
            u.save()
            
            profile = u.get_profile()
                        
            profile.send_activation_email()
            
            return HttpResponseRedirect(reverse('registration.views.activate', 
                                                kwargs={'username': u.username}))
    else: 
        form = UserCreationForm() #unbound form (no data)   
         
    return render_to_response('registration/registration_form.html',
                              {'form': form},
                              context_instance=RequestContext(request))



def resend_activation_code(request, username): 
    
    user = User.objects.get(username=username)
    up = user.get_profile()

    if not user.is_active:
        up.send_activation_email()

        return HttpResponseRedirect(reverse('registration.views.activate', 
                                            kwargs={'username': user.username}))
    return HttpResponseRedirect(reverse('registration.views.login'))


def activate(request, username): 
    set_valid = False
    form = ActivationForm(initial={'username': username})
    if request.method == 'POST': #form submission
        form = ActivationForm(request.POST) #bound form            
        if form.is_valid(): 
            set_valid = True
       
    #link from email
    elif request.GET.get('username') and request.GET.get('activation_key'): 
        form = ActivationForm(initial={'username': request.GET.get('username'),
                                       'activation_key': request.GET.get('activation_key')})        
        if form.is_valid():
            set_valid = True
            
    if set_valid: 
        u = User.objects.get(username=form.cleaned_data['username'])
        u.is_active = True
        u.save()
        return HttpResponseRedirect(reverse('registration.views.login')) 
        
    return render_to_response('registration/activate_form.html',
                              {'form': form, 
                               'username': username},
                              context_instance=RequestContext(request))
