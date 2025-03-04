from datetime import datetime, timedelta, time

from django.core import validators
from django.contrib.auth.models import User, Group
from django.contrib.gis.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

# Create your models here.   

class PharmacyManager(models.Manager):
    
    def create_pharmacy(self, name, pharmacist, phone_number, email, business_hours, location):

        # Add first and last name for the user pharmacist
        User.objects.filter(username=pharmacist['username'])\
            .update(first_name=pharmacist['first_name'], last_name=pharmacist['last_name'])
        
        pharmacist_instance = User.objects.get(username=pharmacist['username'])
        
        pharmacy = self.model(name=name, pharmacist=pharmacist_instance, 
                              phone_number=phone_number, email=email, location=location)
        pharmacy.save(using=self._db)


        for business_hours_data in business_hours:

            # Add pharmacy business hours
            business_hours_instance, created = BusinessHours.objects.get_or_create(
                day_of_the_week=business_hours_data['day_of_the_week'], 
                closed_at=business_hours_data['closed_at'],
                opened_at=business_hours_data['opened_at']
            )

            business_hours_instance.pharmacies.add(pharmacy)

        return pharmacy
    
    
class Pharmacy(models.Model):

    name = models.CharField(max_length=255, unique=True)
    location = models.PointField()
    phone_number = models.CharField(max_length=10, unique=True, validators=[
            validators.RegexValidator(
                regex=r'^09\d{8}$',
                message="Phone number must be in the format 09XXXXXXXX",
                code="invalid_phone_number",
            ),
        ],)
    email = models.EmailField(null=True, unique=True)

    pharmacist = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = PharmacyManager()
    
    def __str__(self) -> str:
        pharmacist_full_name = self.pharmacist.first_name + ' ' + self.pharmacist.last_name
        return self.name + ' | ' + pharmacist_full_name
    

class BusinessHours(models.Model):

    MONDAY = "Mon"
    TUESDAY = "Tue"
    WEDNESDAY = "Wed"
    THIRSDAY = "Thr"
    FRIDAY = "Fri"
    SATURDAY = "Sat"
    SUNDAY = "Sun"

    DAYS_OF_THE_WEEK = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THIRSDAY, "Thirsday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday")
    ]

    day_of_the_week = models.CharField(max_length=3, choices=DAYS_OF_THE_WEEK)
    opened_at = models.TimeField(null=True, blank=True)
    closed_at = models.TimeField(null=True, blank=True)
    
    pharmacies = models.ManyToManyField(Pharmacy, related_name='business_hours')

    class Meta:
        unique_together = ('day_of_the_week', 'opened_at', 'closed_at')
        constraints = [
            models.CheckConstraint(check= (Q(opened_at__isnull=True) & Q(closed_at__isnull=True)) |
                                    Q(opened_at__lt=F('closed_at')), name='opened_at_is_lt_closed_at')
        ]

    def __str__(self) -> str:

        open_at = datetime.combine(datetime.today(), self.opened_at if self.opened_at is not None else time()).time().strftime('%H:%M')
        close_at = datetime.combine(datetime.today(), self.closed_at if self.closed_at is not None else time()).time().strftime('%H:%M')

        return "%s %s %s" % (self.day_of_the_week, open_at, close_at)
