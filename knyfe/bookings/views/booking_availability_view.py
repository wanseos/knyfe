from django.db import models
from django.utils import timezone
from rest_framework import permissions, serializers, views, viewsets

from bookings.models import Booking


class BookingAvailabilityParameterSerializer(serializers.Serializer):
    date_utc = serializers.DateField()


class BookingAvailabilityListAPIView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        serializer = BookingAvailabilityParameterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        date_utc = serializer.validated_data["date_utc"]
        # TODO: segment into hours and calculate availability
        segments = []
        starts_at = timezone.datetime.combine(
            date_utc, timezone.datetime.min.time(), timezone.utc
        )
        # TODO: Optimize this query.
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
                        owner=self.request.user,
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
        return views.Response(segments)
