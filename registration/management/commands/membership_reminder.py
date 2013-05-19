import datetime
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
from django.conf import settings 


from registration.models import Membership

class Command(BaseCommand): 

    def handle(self, *args, **options ): 
        today = datetime.date.today()
        within_month =  today + datetime.timedelta(days=30)
        
        memberships = Membership.objects.filter(valid_thru__lt=within_month,valid_thru__gt=today).all()

        body_msg = get_template('registration/membership_reminder.txt')

        for m in memberships.iterator(): 
            club = m.club
            user = m.user_prof.user
            days_left = m.valid_thru-today

            c = Context({
                'fist_name':m.f_name,
                'club_name':club.name,
                'days_left':days_left,
                'valid_thru_date':m.valid_thru.strftime('%d/%m/%Y'),
                'renewal_link':reverse('renew_membership',kwargs={'club_name':club.safe_name}),
                'renewal_price':club.renew_cost,
                'new_membership_cost':club.new_member_cost,
            })

            subject = "%s Membership Renewal Reminder"%club.name
            body = body_msg.render(c)

            user.email_user(subject, body, settings.DEFAULT_FROM_EMAIL)        


