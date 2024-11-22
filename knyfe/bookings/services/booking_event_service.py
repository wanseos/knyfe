import datetime
import uuid

from django.db import models
from django.utils import timezone

from ..models import BookingEvent, BookingProjection


def generate_key() -> uuid.UUID:
    return uuid.uuid4()


def passed_booking_deadline(starts_at: datetime.datetime) -> bool:
    return starts_at < timezone.now() + timezone.timedelta(days=3)


def handle_booking_created_event(user_id, data: dict) -> BookingProjection:
    """create event and update projection"""
    obj = BookingEvent(
        user_id=user_id,
        timestamp=timezone.now(),
        booking_key=generate_key(),
        event_type=BookingEvent.EventType.CREATED,
        data=data,
    )
    obj.save()
    return _apply_created_event(
        booking_key=obj.booking_key,
        owner_id=obj.data["owner_id"],
        starts_at=obj.data["starts_at"],
        ends_at=obj.data["ends_at"],
        applicants=obj.data["applicants"],
    )


def handle_booking_updated_event(
    user_id,
    booking_key,
    data: dict,
) -> BookingProjection:
    obj = BookingEvent(
        user_id=user_id,
        timestamp=timezone.now(),
        booking_key=booking_key,
        event_type=BookingEvent.EventType.UPDATED,
        data=data,
    )
    obj.save()
    return _apply_updated_event(
        booking_key=obj.booking_key,
        data=obj.data,
    )


def handle_booking_deleted_event(
    user_id,
    booking_key,
) -> tuple:
    event = BookingEvent.objects.create(
        user_id=user_id,
        timestamp=timezone.now(),
        booking_key=booking_key,
        event_type=BookingEvent.EventType.DELETED,
        data={},
    )
    return _apply_deleted_event(booking_key=event.booking_key)


def _apply_created_event(
    booking_key,
    owner_id,
    starts_at,
    ends_at,
    applicants,
):
    return BookingProjection.objects.create(
        booking_key=booking_key,
        owner_id=owner_id,
        starts_at=starts_at,
        ends_at=ends_at,
        applicants=applicants,
        status=BookingProjection.Status.PENDING,
    )


def _apply_updated_event(
    booking_key,
    data: dict,
):
    obj = BookingProjection.objects.get(booking_key=booking_key)
    if "starts_at" in data:
        obj.starts_at = data["starts_at"]
    if "ends_at" in data:
        obj.ends_at = data["ends_at"]
    if "applicants" in data:
        obj.applicants = data["applicants"]
    if "status" in data:
        obj.status = data["status"]
    obj.save()
    return obj


def _apply_deleted_event(booking_key):
    return BookingProjection.objects.filter(booking_key=booking_key).delete()


def handle_list_bookings(user):
    if user.is_staff:
        return BookingProjection.objects.all()
    return BookingProjection.objects.filter(owner=user)


def booking_event_exceeds_capacity(
    starts_at: datetime.datetime,
    ends_at: datetime.datetime,
    user_id: int,
    applicants: int,
) -> bool:
    confirmed_applicants = (
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
    return applicants > 50_000 - confirmed_applicants
