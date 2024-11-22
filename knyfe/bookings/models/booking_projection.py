from django.db import models


class BookingProjection(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        APPROVED = "APPROVED"

    booking_key = models.UUIDField(unique=True, null=False)
    owner = models.ForeignKey("User", on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    applicants = models.IntegerField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
    )

    class Meta:
        db_table = "bookings_bookingprojection"
