from rest_framework import viewsets
from .models import Driver, OrderAssignment, Bids
from orders.models import Order
from accounts.models import Manager
from .serializers import DriverSerializer, BidSerializer

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

class BidViewSet(viewsets.ModelViewSet):
    queryset = Bids.objects.all()
    serializer_class = BidSerializer