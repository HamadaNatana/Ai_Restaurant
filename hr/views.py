from rest_framework.decorators import api_view
from rest_framework.response import Response
from menu.models import Chef
from delivery.models import Driver
from accounts.models import Customer
from .serializers import ChefHRSerializer, DriverHRSerializer, CustomerHRSerializer

# 1. DASHBOARD: Get all lists
@api_view(['GET'])
def hr_dashboard(request):
    chefs = Chef.objects.all()
    drivers = Driver.objects.all()
    customers = Customer.objects.all()
    
    return Response({
        "chefs": ChefHRSerializer(chefs, many=True).data,
        "drivers": DriverHRSerializer(drivers, many=True).data,
        "customers": CustomerHRSerializer(customers, many=True).data
    })

# 2. PROMOTE/DEMOTE CHEF
@api_view(['POST'])
def manage_chef(request, pk):
    try:
        chef = Chef.objects.get(pk=pk)
        action = request.data.get('action') # 'demote' or 'bonus'
        
        if action == 'demote':
            # Business Rule: 2 Demotions = Fired
            chef.demotion_count += 1
            chef.salary = max(0, chef.salary - 500) # Pay cut
            
            if chef.demotion_count >= 2:
                chef.is_active = False # Fired!
                return Response({"message": f"Chef {chef.name} fired due to 2nd demotion."})
                
        elif action == 'bonus':
            chef.salary += 500
            
        chef.save()
        return Response(ChefHRSerializer(chef).data)
    except Chef.DoesNotExist:
        return Response({"error": "Chef not found"}, status=404)

# 3. PROMOTE DRIVER (Performance Bonus)
@api_view(['POST'])
def manage_driver(request, pk):
    try:
        driver = Driver.objects.get(pk=pk)
        action = request.data.get('action') # 'bonus' or 'fire'
        
        if action == 'bonus':
            driver.pay += 100  # Bonus
            
        elif action == 'fire':
            driver.is_active = False
            
        driver.save()
        return Response(DriverHRSerializer(driver).data)
    except Driver.DoesNotExist:
        return Response({"error": "Driver not found"}, status=404)

# 4. KICK CUSTOMER (UC 10)
@api_view(['POST'])
def kick_customer(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
        
        # Business Rule: Clear balance before kicking
        customer.balance = 0
        customer.is_blacklisted = True
        customer.status = 'banned' # Or whatever status David uses for banned
        
        customer.save()
        return Response({"message": f"Customer {customer.user.username} has been blacklisted and funds seized."})
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=404)