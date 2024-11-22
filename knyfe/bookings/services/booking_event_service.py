import uuid

from django.utils import timezone

from ..models import BookingEvent, BookingProjection


def generate_key() -> uuid.UUID:
    return uuid.uuid4()


def create_booking_event(
    booking_key,
    user_id,
    event_type: str,
    data: dict,
) -> BookingEvent:
    obj = BookingEvent(
        user_id=user_id,
        timestamp=timezone.now(),
        booking_key=booking_key,
        event_type=event_type,
        data=data,
    )
    obj.save()
    return obj


def apply_created_event(
    event: BookingEvent,
) -> BookingProjection:
    obj = BookingProjection(
        booking_key=event.booking_key,
        owner_id=event.data["owner_id"],
        starts_at=event.data["starts_at"],
        ends_at=event.data["ends_at"],
        applicants=event.data["applicants"],
        status=BookingProjection.Status.PENDING,
    )
    obj.save()
    return obj


def apply_updated_event(event: BookingEvent) -> BookingProjection:
    obj = BookingProjection.objects.filter(booking_key=event.booking_key).get()
    if "starts_at" in event.data:
        obj.starts_at = event.data["starts_at"]
    if "ends_at" in event.data:
        obj.ends_at = event.data["ends_at"]
    if "applicants" in event.data:
        obj.applicants = event.data["applicants"]
    if "status" in event.data:
        obj.status = event.data["status"]
    obj.save()
    return obj


def apply_deleted_event(booking_key):
    return BookingProjection.objects.filter(booking_key=booking_key).delete()
