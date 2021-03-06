from collections import OrderedDict
import json
import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core import serializers
#from django.views.generic.create_update import create_object, update_object

from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login, logout, password_reset
from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import csrf_exempt

from django.forms import ModelChoiceField, HiddenInput
from django.db.models import Count

from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged

from registration.models import Club, Event, Car, UserProfile, Order, Membership

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
    clubs = Club.objects.select_related().\
            annotate(n_events=Count('seasons__events')).\
            order_by('-n_events')

    for c in clubs: 
        c.current_season = c.sorted_seasons[0]     
        
    context = {'clubs': clubs}

    return render_to_response('registration/clubs.html',
                              context,
                              context_instance=RequestContext(request))

@csrf_exempt
def club(request, club_name): 
    """club detail page"""

    club = Club.objects.select_related().\
            get(safe_name=club_name)  
    member = False        
    if request.user.is_authenticated(): 
        up = request.user.get_profile()
        member = up.is_member(club)

    context = {'club': club,
               'member': member}  

    return render_to_response('registration/club.html',
                              context,
                              context_instance=RequestContext(request))
    
@csrf_exempt
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
def renew_membership(request, club_name): 
    """new club memberships and renewals""" 

    user = request.user
    up = user.get_profile()
    club = Club.objects.get(safe_name=club_name)

    try: 
        m = Membership.objects.get(user_prof=up,club=club,paid=True)
        m.price = club.renew_cost

    except Membership.DoesNotExist: 
        #create new membership 
        m = Membership()
        m.club = club
        m.user_prof = up
        m.price = club.new_member_cost

        m.start = datetime.date.today()
        m.valid_thru = m.start + datetime.timedelta(days=365)

    #create an order
    order = Order()
    order.user_prof = up
    order.save()
    m.order = order
    m.save()

    redirect_target = request.build_absolute_uri(reverse('club_detail',
            kwargs={'club_name': club_name}))

    # What you want the button to do.
    paypal_dict = {
        "business": club.paypal_email,
        #'business': 'jgray-seller@test.com',
        "amount": order.calc_total_price(),
        "item_name": 'Membership for %s '%club.name,
        "invoice": order.pk,
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return_url": redirect_target,
        "cancel_return": redirect_target,

    }
    paypal_form = PayPalPaymentsForm(initial=paypal_dict)

    context={
        'paypal_form': paypal_form.render(),
        'price': paypal_dict['amount'],
        'club': club, 
        'order': order,
        'items': [i.as_leaf_model().cart_name() for i in order.items.all()]
    }    

    return render_to_response('registration/start_pay.html',
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

    reg = None
    if username: 
        reg = e.regs.get(user_profile__user__username=username)

    
    show_cars = bool(Car.objects.filter(user_profile=up, provisional=False).count())
    class UserRegForm(RegForm): #have to create the form here, since it's specific to a user
        
        car = CarChoiceField(queryset=Car.objects.filter(user_profile=up, provisional=False), 
            required=False, empty_label=None)
        event = ModelChoiceField(queryset=Event.objects.filter(pk=e.pk),
                                 initial=e.pk, widget=HiddenInput())
        club = ModelChoiceField(queryset=Club.objects.filter(pk=e.club.pk), 
                                initial=e.club.pk, widget=HiddenInput())
        user_profile = ModelChoiceField(queryset=UserProfile.objects.filter(pk=up.pk),
                                        initial=up.pk, widget=HiddenInput())

        def __init__(self,*args,**kwargs): 
            super(UserRegForm, self).__init__(*args,**kwargs)

            if not show_cars: 
                self.fields['car'].widget=HiddenInput()

            if reg and reg.paid: #hide reg if paid
                self.fields['prepay'].widget=HiddenInput()
                self.fields['coupon_code'].widget=HiddenInput()



    

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
                if form.coupon: 
                    order.coupon = form.coupon
                    order.coupon.uses_left -= 1
                order.save()
                reg.order = order
                reg.save()

                # What you want the button to do.
                paypal_dict = {
                    "business": e.club.paypal_email,
                    #'business': 'jgray-seller@test.com',
                    "amount": order.calc_total_price(),
                    "item_name": 'Registration for %s %s'%(e.club.name, e.name),
                    "invoice": order.pk,
                    "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
                    "return_url": request.build_absolute_uri(redirect_target),
                    "cancel_return": request.build_absolute_uri(redirect_target),

                }

                if paypal_dict['amount']=='0.00': #don't need to pay if the price is 0
                    order.payment_complete()
                    return HttpResponseRedirect(redirect_target)
                else: 
                    paypal_form = PayPalPaymentsForm(initial=paypal_dict)
     
                    context={
                        'paypal_form': paypal_form.render(),
                        'price': paypal_dict['amount'],
                        'club': e.club, 
                        'order': order,
                        'items': [i.as_leaf_model().cart_name() for i in order.items.all()]
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

#ipn notification signal 
def payment_complete(sender, **kwargs):
    ipn_obj = sender
    # Undertake some action depending upon `ipn_obj`.

    o = Order.objects.get(pk=ipn_obj.invoice)
    o.payment_complete()

payment_was_successful.connect(payment_complete)

def payment_failed(sender, **kwargs):
    ipn_obj = sender
    # Undertake some action depending upon `ipn_obj`.
    
    o = Order.objects.get(pk=ipn_obj.invoice)
    o.payment_failed()

payment_was_flagged.connect(payment_failed)

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
            u.first_name = form.cleaned_data['first_name']
            u.last_name = form.cleaned_data['last_name']
            
            u.save()
            
            profile = u.get_profile()
                        
            profile.send_activation_email(request)
            
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
        up.send_activation_email(request)

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
