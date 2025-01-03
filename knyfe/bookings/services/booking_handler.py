import dataclasses
import datetime
import typing
import uuid

from django.db import transaction
from django.utils import timezone
from typing_extensions import NotRequired
from utils.result import Result

from ..models import User
from . import booking_event_service, booking_projection_service


class CreateData(typing.TypedDict):
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    applicants: int


class BookingData(typing.TypedDict):
    booking_key: uuid.UUID
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    applicants: int
    status: str


def handle_create(user: User, data: CreateData) -> Result[BookingData, str]:
    """create booking event and update projection"""
    if not _validate_booking_capacity(
        starts_at=data["starts_at"],
        ends_at=data["starts_at"],
        user_id=user.pk,
        applicants=data["applicants"],
    ):
        return Result(error="Applicants must be under booking capacity per slot.")
    if not _validate_applicants(data["applicants"]):
        return Result(error="Applicants must be a positive integer.")
    if not _validate_starts_at(data["starts_at"]):
        return Result(error="Booking must be made at least 3 days in advance.")
    with transaction.atomic():
        event = booking_event_service.create_booking_event(
            booking_key=booking_event_service.generate_key(),
            user_id=user.pk,
            event_type="CREATED",
            data={
                "owner_id": user.pk,
                "starts_at": data["starts_at"].isoformat(),
                "ends_at": data["ends_at"].isoformat(),
                "applicants": data["applicants"],
            },
        )
        obj = booking_event_service.apply_created_event(event)
    return Result(
        value={
            "booking_key": obj.booking_key,
            "starts_at": obj.starts_at,
            "ends_at": obj.ends_at,
            "applicants": obj.applicants,
            "status": obj.status,
        }
    )


class UpdateData(typing.TypedDict):
    starts_at: NotRequired[datetime.datetime]
    ends_at: NotRequired[datetime.datetime]
    applicants: NotRequired[int]


def handle_update(
    user: User, booking_key: uuid.UUID, data: UpdateData
) -> Result[BookingData, str]:
    try:
        obj = booking_projection_service.query_by_booking_key(booking_key=booking_key)
    except booking_projection_service.BookingProjection.DoesNotExist:
        return Result(error="Booking not found").with_metadata("status", 404)
    if not user.is_staff and obj.owner_id != user.pk:
        return Result(error="Booking not found").with_metadata("status", 404)
    # TODO: optimize and simplify partial update.
    if "starts_at" not in data:
        data["starts_at"] = obj.starts_at
    if "ends_at" not in data:
        data["ends_at"] = obj.ends_at
    if "applicants" not in data:
        data["applicants"] = obj.applicants
    if not _validate_status_for_modification(user, obj.status):
        return Result(error="Confirmed booking cannot be updated").with_metadata(
            "status", 400
        )
    if not _validate_booking_capacity(
        starts_at=data["starts_at"],
        ends_at=data["ends_at"],
        user_id=user.pk,
        applicants=data["applicants"],
    ):
        return Result(error="Applicants must be under booking capacity per slot.")
    if not _validate_applicants(data["applicants"]):
        return Result(error="Applicants must be a positive integer.")
    if not _validate_starts_at(data["starts_at"]):
        return Result(error="Booking must be made at least 3 days in advance.")
    with transaction.atomic():
        event = booking_event_service.create_booking_event(
            booking_key=booking_key,
            user_id=user.pk,
            event_type="UPDATED",
            data={
                "starts_at": data["starts_at"].isoformat(),
                "ends_at": data["ends_at"].isoformat(),
                "applicants": data["applicants"],
            },
        )
        obj = booking_event_service.apply_updated_event(event)
    return Result(
        value={
            "booking_key": obj.booking_key,
            "starts_at": obj.starts_at,
            "ends_at": obj.ends_at,
            "applicants": obj.applicants,
            "status": obj.status,
        }
    )


def handle_delete(user: User, booking_key: uuid.UUID) -> Result[None, str]:
    try:
        obj = booking_projection_service.query_by_booking_key(booking_key=booking_key)
    except booking_projection_service.BookingProjection.DoesNotExist:
        return Result(error="Booking not found").with_metadata("status", 404)
    if not user.is_staff and obj.owner_id != user.pk:
        return Result(error="Booking not found").with_metadata("status", 404)
    if not _validate_status_for_modification(user, obj.status):
        return Result(error="Confirmed booking cannot be deleted").with_metadata(
            "status", 400
        )
    with transaction.atomic():
        event = booking_event_service.create_booking_event(
            booking_key=booking_key,
            user_id=user.pk,
            event_type="DELETED",
            data={},
        )
        booking_event_service.apply_deleted_event(event.booking_key)
    return Result(None, error=None)


def handle_approve(user: User, booking_key: uuid.UUID) -> Result[BookingData, str]:
    with transaction.atomic():
        event = booking_event_service.create_booking_event(
            booking_key=booking_key,
            user_id=user.pk,
            event_type="UPDATED",
            data={"status": "APPROVED"},
        )
        obj = booking_event_service.apply_updated_event(event)
    return Result(
        value={
            "booking_key": obj.booking_key,
            "starts_at": obj.starts_at,
            "ends_at": obj.ends_at,
            "applicants": obj.applicants,
            "status": obj.status,
        }
    )


def handle_list(user: User) -> typing.List[BookingData]:
    if user.is_staff:
        qs = booking_projection_service.query_booking_projections()
    else:
        qs = booking_projection_service.query_booking_projections_by_owner(
            owner_id=user.pk
        )
    return [
        {
            "booking_key": obj.booking_key,
            "starts_at": obj.starts_at,
            "ends_at": obj.ends_at,
            "applicants": obj.applicants,
            "status": obj.status,
        }
        for obj in qs
    ]


def handle_retrieve(user: User, booking_key: uuid.UUID) -> Result[BookingData, str]:
    try:
        obj = booking_projection_service.query_by_booking_key(booking_key=booking_key)
    except booking_projection_service.BookingProjection.DoesNotExist:
        return Result(error="Booking not found").with_metadata("status", 404)
    if not user.is_staff and obj.owner_id != user.pk:
        return Result(error="Booking not found").with_metadata("status", 404)
    return Result(
        value={
            "booking_key": obj.booking_key,
            "starts_at": obj.starts_at,
            "ends_at": obj.ends_at,
            "applicants": obj.applicants,
            "status": obj.status,
        }
    )


@dataclasses.dataclass
class BookingAvailability:
    index: int
    remaining: int


def handle_list_availability(
    date: datetime.date,
    user_id: int,
) -> typing.List[BookingAvailability]:
    data = booking_projection_service.query_booking_projection_applicants_by_hour(
        date=date, user_id=user_id
    )
    return [
        BookingAvailability(
            index=row[0],
            remaining=booking_projection_service.get_booking_capacity() - row[1],
        )
        for row in data
    ]


# validators
def _validate_booking_capacity(
    starts_at: datetime.datetime,
    ends_at: datetime.datetime,
    user_id: int,
    applicants: int,
) -> bool:
    return applicants <= booking_projection_service.query_remaining_capacity(
        starts_at=starts_at,
        ends_at=ends_at,
        user_id=user_id,
    )


def _validate_applicants(value: int):
    return value > 0


def _validate_starts_at(value: datetime.datetime):
    return value > timezone.now() + timezone.timedelta(days=3)


def _validate_status_for_modification(user: User, status: str):
    if user.is_staff:
        return True
    if status != "PENDING":
        return False
    return True
