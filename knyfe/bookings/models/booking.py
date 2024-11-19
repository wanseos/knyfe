from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        APPROVED = "APPROVED"

    key = models.UUIDField(unique=True, null=False)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()  # inclusive start
    ends_at = models.DateTimeField()  # exclusive end
    applicants = models.IntegerField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        db_table = "bookings_booking"
