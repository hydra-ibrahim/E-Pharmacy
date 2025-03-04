from django.urls import path
from .views import PharmacyView

urlpatterns = [
    path("pharmacies/", PharmacyView.as_view({'get':'list', 'post':'create'}), name="pharmacies"),
]
