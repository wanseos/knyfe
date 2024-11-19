import uuid

from django.db import models
from django.utils import timezone
from rest_framework import permissions, response, serializers, viewsets
from rest_framework.decorators import action

from bookings.models import Booking


class BookingSerializer(serializers.ModelSerializer):
    # TODO: Implement value validation. e.g. starts_at < ends_at
    # positive integer for applicants
    # applicants under booking_capacity_per_slot
    class Meta:
        model = Booking
        fields = [
            "key",
            "starts_at",
            "ends_at",
            "applicants",
            "status",
            "owner",
        ]
        read_only_fields = ["key", "status", "owner"]

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
    permission_classes = [permissions.IsAuthenticated]

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

    @action(
        detail=True, methods=["PATCH"], permission_classes=[permissions.IsAdminUser]
    )
    def approve(self, request, key):
        booking = self.get_object()
        if booking.status != "PENDING":
            raise serializers.ValidationError("Cannot approve confirmed booking.")
        booking.status = "APPROVED"
        return response.Response(BookingSerializer(booking).data)
