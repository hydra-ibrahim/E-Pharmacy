
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Pharmacy
from .serializers import PharmacySerializer

from rest_framework_gis.filters import DistanceToPointOrderingFilter


class PharmacyView(viewsets.ModelViewSet):

    queryset = Pharmacy.objects.all()

    serializer_class = PharmacySerializer
    
    distance_ordering_filter_field = 'location' # The spatial field in the model
    filter_backends = (DistanceToPointOrderingFilter,)

    lookup_field = 'pharmacy'
    

    def get_permissions(self):

        if self.action == 'create':
            permission_classes = [IsAuthenticated & IsAdminUser]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    