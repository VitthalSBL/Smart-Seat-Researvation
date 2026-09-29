from django.contrib import admin
from .models import Seat

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("label", "status", "reserved_by", "reserved_until", "booked_by")
    list_filter = ("status",)
