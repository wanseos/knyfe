import datetime
import typing
import uuid

from django.db import connection, models
from django.utils import timezone

from ..models import BookingProjection


def get_booking_capacity() -> int:
    return 50_000


def query_by_booking_key(booking_key: uuid.UUID) -> BookingProjection:
    return BookingProjection.objects.get(booking_key=booking_key)


def query_booking_projections_by_owner(owner_id: int):
    if not owner_id:
        return BookingProjection.objects.none()
    return BookingProjection.objects.filter(owner_id=owner_id)


def query_booking_projections():
    return BookingProjection.objects.filter()


def query_remaining_capacity(
    starts_at: datetime.datetime,
    ends_at: datetime.datetime,
    user_id: int,
) -> int:
    return get_booking_capacity() - (
        (
            BookingProjection.objects.filter(
                status=BookingProjection.Status.APPROVED,
                owner_id=user_id,
                starts_at__gte=starts_at,
                ends_at__lt=ends_at,
            ).aggregate(total_applicants=models.Sum("applicants"))["total_applicants"]
        )
        or 0
    )


def query_booking_projection_applicants_by_hour(
    date: datetime.date,
    user_id: int,
) -> typing.List[typing.Tuple[int, int]]:
    starts_at = timezone.datetime.combine(
        date, timezone.datetime.min.time(), timezone.utc
    )
    query = """
WITH intervals AS (
    SELECT
        generate_series(
            %s::timestamptz,
            %s::timestamptz,
            '1 hour'
        ) AS start_time
),
bookings_with_intervals AS (
    SELECT
        i.start_time,
        i.start_time + interval '1 hour' AS end_time,
        COALESCE(b.applicants, 0) AS applicants
    FROM intervals i
    LEFT JOIN bookings_bookingprojection b
    ON b.owner_id = %s
       AND b.status = 'APPROVED'
       AND (
           b.starts_at BETWEEN i.start_time AND i.start_time + interval '1 hour' OR
           b.ends_at BETWEEN i.start_time AND i.start_time + interval '1 hour'
       )
)
SELECT
    EXTRACT(HOUR FROM start_time)::INT AS hour_index,
    SUM(applicants) AS total_applicants
FROM bookings_with_intervals
GROUP BY hour_index
ORDER BY hour_index;
"""
    params = [starts_at, starts_at + timezone.timedelta(hours=23), user_id]
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()
