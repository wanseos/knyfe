from django.utils import timezone
from django.db import models
import uuid
from rest_framework import permissions, viewsets, serializers, views

from bookings.models import Booking


class IsAdminUserOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        if "status" in request.data:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.owner == request.user


class BookingSerializer(serializers.ModelSerializer):
    # TODO: Implement value validation. e.g. starts_at < ends_at
    # positive integer for applicants
    # applicants under booking_capacity_per_slot
    class Meta:
        model = Booking
        fields = ["key", "starts_at", "ends_at", "applicants", "status"]
        read_only_fields = ["key"]
        extra_kwargs = {
            "status": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["key"] = uuid.uuid4()
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def validate_applicants(self, value):
        if value <= 0:
            raise serializers.ValidationError("Applicants must be a positive integer.")
        # TODO: Extract into services.
        confirmed_applicants = (
            (
                Booking.objects.filter(
                    status="CONFIRMED",
                    owner=self.context["request"].user,
                    starts_at__gte=self.initial_data["starts_at"],
                    ends_at__lt=self.initial_data["ends_at"],
                ).aggregate(total_applicants=models.Sum("applicants"))[
                    "total_applicants"
                ]
            )
            or 0
        )
        if value > 50_000 - confirmed_applicants:
            raise serializers.ValidationError(
                "Applicants must be under booking capacity per slot."
            )
        return value

    def validate_starts_at(self, value):
        if value < timezone.now() + timezone.timedelta(days=3):
            raise serializers.ValidationError(
                "Booking must be made at least 3 days in advance."
            )
        return value


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    lookup_field = "key"
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrOwner]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(owner=self.request.user)
        return qs

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            if serializer.instance.status != "PENDING":
                raise serializers.ValidationError("Cannot update confirmed booking.")
            if "status" in serializer.validated_data:
                raise serializers.ValidationError("Cannot update status.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            # TODO: Extract into services.
            if instance.status != "PENDING":
                raise serializers.ValidationError("Cannot delete confirmed booking.")
        return super().perform_destroy(instance)


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
