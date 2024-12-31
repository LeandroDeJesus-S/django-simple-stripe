from django.contrib import admin
from .models import Address, AddressLines


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    ...


@admin.register(AddressLines)
class AddressLinesAdmin(admin.ModelAdmin):
    ...
