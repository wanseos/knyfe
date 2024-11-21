import datetime
import uuid

from django.db import models

from ..models import Booking


def generate_key() -> uuid.UUID:
    return uuid.uuid4()


def get_booking_capacity() -> int:
    return 50_000


def exceeds_capacity(
    starts_at: datetime.datetime,
    ends_at: datetime.datetime,
    user_id: int,
    applicants: int,
) -> bool:
    confirmed_applicants = (
        (
            Booking.objects.filter(
                status=Booking.Status.APPROVED,
                owner_id=user_id,
                starts_at__gte=starts_at,
                ends_at__lt=ends_at,
            ).aggregate(total_applicants=models.Sum("applicants"))["total_applicants"]
        )
        or 0
    )
    return applicants > get_booking_capacity() - confirmed_applicants
