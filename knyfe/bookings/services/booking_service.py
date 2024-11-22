import datetime
import uuid

from django.utils import timezone

# TODO: Refactor to use booking event, and remove this service.


def generate_key() -> uuid.UUID:
    return uuid.uuid4()


def get_booking_capacity() -> int:
    return 50_000


def passed_booking_deadline(starts_at: datetime.datetime) -> bool:
    return starts_at < timezone.now() + timezone.timedelta(days=3)
