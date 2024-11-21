import dataclasses
import datetime
import typing

from django.db import models
from django.utils import timezone

from ..models import Booking
from . import booking_service


@dataclasses.dataclass
class BookingAvailability:
    index: int
    remaining: int


def query_availabilities(
    date: datetime.date,
    user_id: int,
) -> typing.List[BookingAvailability]:
    segments = []
    starts_at = timezone.datetime.combine(
        date, timezone.datetime.min.time(), timezone.utc
    )
    qs = Booking.objects.filter(
        status=Booking.Status.APPROVED,
        owner_id=user_id,
    )
    for h in range(24):
        new_st = starts_at + timezone.timedelta(hours=h)
        new_et = starts_at + timezone.timedelta(hours=h + 1)
        confirmed_applicants = (
            (
                qs.filter(
                    models.Q(
                        models.Q(starts_at__range=(new_st, new_et))
                        | models.Q(ends_at__range=(new_st, new_et))
                    )
                ).aggregate(total_applicants=models.Sum("applicants"))[
                    "total_applicants"
                ]
            )
            or 0
        )
        segments.append(
            BookingAvailability(
                index=h,
                remaining=booking_service.get_booking_capacity() - confirmed_applicants,
            )
        )
    return segments
