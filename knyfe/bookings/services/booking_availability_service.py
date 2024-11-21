import dataclasses
import datetime
import typing

from django.db import connection
from django.utils import timezone

from . import booking_service


@dataclasses.dataclass
class BookingAvailability:
    index: int
    remaining: int


def query_availabilities(
    date: datetime.date,
    user_id: int,
) -> typing.List[BookingAvailability]:
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
    LEFT JOIN bookings_booking b
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
        data = cursor.fetchall()
    return [
        BookingAvailability(
            index=row[0], remaining=booking_service.get_booking_capacity() - row[1]
        )
        for row in data
    ]
