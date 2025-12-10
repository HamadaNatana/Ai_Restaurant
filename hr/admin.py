from django.contrib import admin
from .models import HRAction, AssignmentMemo, RegistrationApproval

admin.site.register(HRAction)
admin.site.register(AssignmentMemo)
admin.site.register(RegistrationApproval)