from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Pharmacy, BusinessHours
from django.contrib.gis.forms.widgets import OSMWidget

class CustomOSMWidget(OSMWidget):
    default_lon = 35.79011
    default_lat = 35.53168
    default_zoom = 12

# Register your models here.
@admin.register(Pharmacy)
class PharmacyAdmin(GISModelAdmin):
    gis_widget = CustomOSMWidget
    list_display = ['name', 'location']

admin.site.register(BusinessHours)
