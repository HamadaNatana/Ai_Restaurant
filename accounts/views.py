from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from hr.models import RegistrationApproval
from .models import Customer
from .serializers import CustomerSerializer
from django.contrib.auth import authenticate 

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        # Assumes the User model has a related object named 'customer'
        customer = request.user.customer 
        serializer = self.get_serializer(customer)
        return Response(serializer.data)

class RegistrationAPIView(APIView):
    permission_classes = () # Allow unauthenticated access
    
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        address = request.data.get("address", "")

        # 1. Basic validation
        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Business/Security validation
        if Customer.objects.filter(username=username, is_blacklisted=True).exists():
            return Response({"error": "This account has been blocked."}, status=status.HTTP_403_FORBIDDEN)

        if Customer.objects.filter(username=username).exists():
            return Response({"error": "This username is already in use."}, status=status.HTTP_409_CONFLICT)

        if RegistrationApproval.objects.filter(username=username, status=RegistrationApproval.STATUS_PENDING).exists():
            return Response({"error": "There is already a pending registration."}, status=status.HTTP_409_CONFLICT)

        # 3. Securely create the approval record
        hashed_password = make_password(password)
        RegistrationApproval.objects.create(
            username=username,
            password_hash=hashed_password,   
            address=address,
            status=RegistrationApproval.STATUS_PENDING
        )

        return Response(
            {"message": "Registration request submitted. A manager must approve it."},
            status=status.HTTP_202_ACCEPTED
        )

class LoginAPIView(APIView):
    permission_classes = () 

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            # Check blacklist (UC3 logic)
            if user.is_blacklisted:
                return Response({"error": "Your account has been blocked."}, status=status.HTTP_403_FORBIDDEN)
            
            customer = user.customer # Assuming 1:1 relation to Customer model

            # Build warning info (UC15 logic)
            warning_msg = build_warning_message(customer)

            # NOTE: You must replace this placeholder with actual token generation code 
            # (e.g., Simple JWT's token_obtain_pair view logic)
            return Response({
                "token": "YOUR_GENERATED_JWT_TOKEN", 
                "username": user.username,
                "warning_message": warning_msg
            })
        else:
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# UC15: Customer views their accumilated warnings when they log in
def build_warning_message(customer: Customer) -> str | None:
    if customer.warnings == 0:
        return None

    if customer.status == Customer.STATUS_VIP:
        return f"You currently have {customer.warnings} warning(s). VIPs are demoted after 2 warnings."
    else:
        return f"You currently have {customer.warnings} warning(s). Registered customers are removed after 3 warnings."