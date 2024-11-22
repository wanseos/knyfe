from drf_spectacular.utils import extend_schema
from rest_framework import permissions, response, serializers, status, viewsets
from rest_framework.decorators import action

from ..models import BookingProjection, User
from ..services import booking_event_handler, booking_event_service


class BookingSerializer(serializers.Serializer):
    booking_key = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=BookingProjection.Status.choices, required=False
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    applicants = serializers.IntegerField()

    class Meta:
        read_only_fields = ["booking_key", "status", "owner"]

    def validate_applicants(self, value):
        if value <= 0:
            raise serializers.ValidationError("Applicants must be a positive integer.")
        return value

    def validate_starts_at(self, value):
        if booking_event_service.passed_booking_deadline(value):
            raise serializers.ValidationError(
                "Booking must be made at least 3 days in advance."
            )
        return value

    def update(self, instance, validated_data):
        current_user = self.context["request"].user
        if booking_event_service.booking_event_exceeds_capacity(
            self.validated_data.get("starts_at", instance.starts_at),
            self.validated_data.get("ends_at", instance.ends_at),
            current_user.id,
            validated_data.get("applicants", instance.applicants),
        ):
            raise serializers.ValidationError(
                "Applicants must be under booking capacity per slot."
            )
        data = {}
        if "starts_at" in validated_data:
            data["starts_at"] = validated_data["starts_at"].isoformat()
        if "ends_at" in validated_data:
            data["ends_at"] = validated_data["ends_at"].isoformat()
        if "applicants" in validated_data:
            data["applicants"] = validated_data["applicants"]
        obj = booking_event_service.handle_update_booking(
            user_id=current_user.id,
            booking_key=instance.booking_key,
            data=data,
        )
        return obj


class BookingViewSet(viewsets.ViewSet):
    lookup_field = "key"
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        current_user = request.user
        qs = booking_event_service.handle_list_bookings(current_user)
        return response.Response(
            BookingSerializer(qs, many=True).data, status=status.HTTP_200_OK
        )

    def retrieve(self, request, key):
        current_user = request.user
        try:
            obj = booking_event_service.handle_retrieve_booking(
                user=current_user,
                booking_key=key,
            )
        except BookingProjection.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        return response.Response(
            BookingSerializer(obj).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=BookingSerializer,
        responses={201: BookingSerializer},
    )
    def create(self, request):
        # TODO: Refactor and add schema documentation.
        ser = BookingSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        request_data = ser.validated_data
        result = booking_event_handler.handle_create(
            user=request.user,
            data={
                "starts_at": request_data["starts_at"],
                "ends_at": request_data["ends_at"],
                "applicants": request_data["applicants"],
            },
        )

        if result.is_error():
            status_code = result.get_metadata(
                "status_code", status.HTTP_400_BAD_REQUEST
            )
            raise serializers.ValidationError(result.unwrap_error(), code=status_code)

        return response.Response(
            BookingSerializer(result.unwrap()).data,
            status=result.get_metadata("status_code", status.HTTP_201_CREATED),
        )

    def partial_update(self, request, key):
        try:
            obj = booking_event_service.handle_retrieve_booking(
                user=request.user,
                booking_key=key,
            )
        except BookingProjection.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        if (
            not request.user.is_staff
            and obj.status == BookingProjection.Status.APPROVED
        ):
            return response.Response(
                {"error": "Approved booking cannot be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = BookingSerializer(
            obj, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, key):
        try:
            obj = booking_event_service.handle_retrieve_booking(
                user=request.user,
                booking_key=key,
            )
        except BookingProjection.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        if (
            not request.user.is_staff
            and obj.status == BookingProjection.Status.APPROVED
        ):
            return response.Response(
                {"error": "Approved booking cannot be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = BookingSerializer(
            obj, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, key):
        try:
            obj = booking_event_service.handle_retrieve_booking(
                user=request.user,
                booking_key=key,
            )
        except BookingProjection.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        if (
            not request.user.is_staff
            and obj.status == BookingProjection.Status.APPROVED
        ):
            return response.Response(
                {"error": "Approved booking cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking_event_service.handle_delete_booking(
            user_id=request.user.id,
            booking_key=key,
        )
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["PATCH"],
        permission_classes=[permissions.IsAdminUser],
    )
    def approve(self, request, key):
        current_user = request.user
        obj = booking_event_service.handle_update_booking(
            user_id=current_user.id,
            booking_key=key,
            data={"status": BookingProjection.Status.APPROVED},
        )
        return response.Response(
            BookingSerializer(obj).data,
            status=status.HTTP_200_OK,
        )
