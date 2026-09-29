from django.conf import settings
from django.db import models

HOLD_SECONDS = 120  # 2 minutes


class Seat(models.Model):
    AVAILABLE, RESERVED, BOOKED = "available", "reserved", "booked"
    STATUS_CHOICES = [(AVAILABLE, "Available"), (RESERVED, "Reserved"), (BOOKED, "Booked")]

    label = models.CharField(max_length=10, unique=True)  # e.g. A1
    row = models.CharField(max_length=2)
    number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=AVAILABLE, db_index=True)
    reserved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="held_seats")
    reserved_until = models.DateTimeField(null=True, blank=True)
    booked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="booked_seats")
    booked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["row", "number"]

    def __str__(self):
        return f"{self.label} ({self.status})"
