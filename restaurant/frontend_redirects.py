from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Customer, Manager


def get_role(user):
    """
    Detects role based on logged-in user.
    """
    # Manager
    if Manager.objects.filter(user=user).exists():
        return "MANAGER"

    # Customer
    try:
        cust = Customer.objects.get(id=user.id)
    except Customer.DoesNotExist:
        return "VISITOR"

    if cust.status == Customer.STATUS_VIP:
        return "VIP"
    return "CUSTOMER"


@login_required
def ai_chat_redirect(request):
    """
    After login, redirect to Streamlit AI Chat.
    """
    username = request.user.username
    role = get_role(request.user)

    url = f"http://localhost:8506/ai_chat_streamlit?username={username}&role={role}"
    return redirect(url)


@login_required
def discussion_redirect(request):
    """
    Redirect to Streamlit Discussion Board.
    """
    username = request.user.username
    role = get_role(request.user)

    url = f"http://localhost:8506/discussion?username={username}&role={role}"
    return redirect(url)


@login_required
def allergy_redirect(request):
    """
    Redirect to Streamlit Allergy Preferences.
    """
    username = request.user.username
    role = get_role(request.user)

    url = f"http://localhost:8506/allergy?username={username}&role={role}"
    return redirect(url)
