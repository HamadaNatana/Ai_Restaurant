from django.contrib import admin
from .models import Chef, Dish, Ingredient, Allergen, AllergyPreference

admin.site.register(Chef)
admin.site.register(Dish)
admin.site.register(Ingredient)
admin.site.register(Allergen)
@admin.register(AllergyPreference)
class AllergyPreferenceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'display_allergies_count', 'created_at'] 
    def display_allergies_count(self, obj):
        return obj.allergies.count()
    display_allergies_count.short_description = "Allergy Count"