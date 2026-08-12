from django.contrib import admin

from pharmacy_app.models import Medicine


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "manufacturer", "unit_price", "stock_quantity", "expiry_date", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "generic_name", "manufacturer", "batch_number"]
