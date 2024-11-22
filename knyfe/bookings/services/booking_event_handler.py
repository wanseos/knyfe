import datetime
import typing
import uuid

from django.db import models
from django.utils import timezone
from utils.result import Result

from ..models import BookingProjection, User
from ..services import booking_event_service


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
    obj = booking_event_service.handle_create(
        user_id=user.pk,
        data={
            "owner_id": user.pk,
            "starts_at": data["starts_at"].isoformat(),
            "ends_at": data["ends_at"].isoformat(),
            "applicants": data["applicants"],
        },
    )
    return Result(
        value={
            "booking_key": obj.booking_key,
            "starts_at": obj.starts_at,
            "ends_at": obj.ends_at,
            "applicants": obj.applicants,
            "status": obj.status,
        }
    )


def _validate_booking_capacity(
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
    return (
        applicants
        <= booking_event_service.get_booking_capacity() - confirmed_applicants
    )


def _validate_applicants(value: int):
    return value > 0


def _validate_starts_at(value: datetime.datetime):
    return value > timezone.now() + timezone.timedelta(days=3)
