import datetime
import typing

from django.db import models
from django.utils import timezone

from ..models import Booking


def query_availabilities(
    date: datetime.date, user
) -> typing.List[typing.Dict[str, typing.Union[int, str]]]:
    segments = []
    starts_at = timezone.datetime.combine(
        date, timezone.datetime.min.time(), timezone.utc
    )
    for h in range(24):
        new_st = starts_at + timezone.timedelta(hours=h)
        new_et = starts_at + timezone.timedelta(hours=h + 1)
        confirmed_applicants = (
            (
                Booking.objects.filter(
                    models.Q(
                        models.Q(starts_at__range=(new_st, new_et))
                        | models.Q(ends_at__range=(new_st, new_et))
                    ),
                    status="APPROVED",
                    owner=user,
                ).aggregate(total_applicants=models.Sum("applicants"))[
                    "total_applicants"
                ]
            )
            or 0
        )
        segments.append(
            {
                "index": h,
                "remaining": 50_000 - confirmed_applicants,
            }
        )
    return segments
