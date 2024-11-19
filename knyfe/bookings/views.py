import uuid
from rest_framework import permissions, viewsets, serializers

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
