from django.db import models


class BookingEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "CREATED"
        UPDATED = "UPDATED"
        DELETED = "DELETED"

    user_id = models.IntegerField()
    booking_key = models.UUIDField(null=False, db_index=True)
    event_type = models.CharField(
        max_length=10,
        choices=EventType.choices,
    )
    timestamp = models.DateTimeField()
    data = models.JSONField()

    class Meta:
        db_table = "bookings_bookingevent"
