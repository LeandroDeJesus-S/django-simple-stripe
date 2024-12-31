from django.contrib import admin
from .models import StripeCustomer


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'user', 'idempotency_key']
