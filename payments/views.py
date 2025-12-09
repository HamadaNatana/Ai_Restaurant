from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Transactions
from accounts.models import Customer
# UC8: Customer deposits money into acount
@login_required
def deposit_view(request):
    if request.method == "POST":
        amount = request.POST.get("amount")

        # Validate input
        try:
            amount = float(amount)
        except:
            messages.error(request, "Invalid amount.")
            return render(request, "payments/deposit.html")

        if amount <= 0:
            messages.error(request, "Deposit amount must be positive.")
            return render(request, "payments/deposit.html")
        
        if amount >= 100000:
            messages.error(request, "Deposit amount is too excessive")
            return render(request, "payments/deposit.html")

        customer: Customer = request.user
        customer.balance += amount
        customer.save()

        Transactions.objects.create(
            customer=customer,
            type=Transactions.TYPE_DEPOSIT,
            amount=amount,
        )

        messages.success(request, f"Deposit successful! Your new balance is ${customer.balance}.")
        return redirect("deposit")

    return render(request, "payments/deposit.html")
