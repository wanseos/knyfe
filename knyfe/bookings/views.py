from drf_spectacular.utils import extend_schema
from rest_framework import (
    permissions,
    response,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action, api_view, permission_classes

from .models import BookingProjection
from .services import booking_handler


class BookingSerializer(serializers.Serializer):
    booking_key = serializers.UUIDField()
    status = serializers.ChoiceField(choices=BookingProjection.Status.choices)
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    applicants = serializers.IntegerField()

    class Meta:
        read_only_fields = ["booking_key", "status"]


class BookingCreateSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField(required=True)
    ends_at = serializers.DateTimeField(required=True)
    applicants = serializers.IntegerField(required=True)


class BookingUpdateSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField(required=False)
    ends_at = serializers.DateTimeField(required=False)
    applicants = serializers.IntegerField(required=False)


class BookingViewSet(viewsets.ViewSet):
    lookup_field = "booking_key"
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: BookingSerializer(many=True)},
    )
    def list(self, request):
        data = booking_handler.handle_list(user=request.user)
        return response.Response(
            data=BookingSerializer(data, many=True).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={200: BookingSerializer},
    )
    def retrieve(self, request, booking_key):
        result = booking_handler.handle_retrieve(
            user=request.user,
            booking_key=booking_key,
        )
        if result.is_error():
            return response.Response(
                {"error": result.unwrap_error()},
                status=result.get_metadata("status", status.HTTP_400_BAD_REQUEST),
            )
        return response.Response(
            BookingSerializer(result.unwrap()).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: BookingSerializer},
    )
    def create(self, request):
        request_serializer = BookingCreateSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_data = request_serializer.validated_data
        result = booking_handler.handle_create(
            user=request.user,
            data=request_data,
        )

        if result.is_error():
            return response.Response(
                {"error": result.unwrap_error()},
                status=result.get_metadata("status", status.HTTP_400_BAD_REQUEST),
            )
        return response.Response(
            BookingSerializer(result.unwrap()).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=BookingUpdateSerializer,
        responses={200: BookingSerializer},
    )
    def partial_update(self, request, booking_key):
        request_serializer = BookingUpdateSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_data = request_serializer.validated_data
        result = booking_handler.handle_update(
            user=request.user,
            booking_key=booking_key,
            data=request_data,
        )
        if result.is_error():
            return response.Response(
                {"error": result.unwrap_error()},
                status=result.get_metadata("status", status.HTTP_400_BAD_REQUEST),
            )
        return response.Response(
            BookingSerializer(result.unwrap()).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=BookingUpdateSerializer,
        responses={200: BookingSerializer},
    )
    def update(self, request, booking_key):
        request_serializer = BookingUpdateSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_data = request_serializer.validated_data
        result = booking_handler.handle_update(
            user=request.user,
            booking_key=booking_key,
            data={
                "starts_at": request_data["starts_at"],
                "ends_at": request_data["ends_at"],
                "applicants": request_data["applicants"],
            },
        )
        if result.is_error():
            return response.Response(
                {"error": result.unwrap_error()},
                status=result.get_metadata("status", status.HTTP_400_BAD_REQUEST),
            )
        return response.Response(
            BookingSerializer(result.unwrap()).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={204: None},
    )
    def destroy(self, request, booking_key):
        result = booking_handler.handle_delete(
            user=request.user,
            booking_key=booking_key,
        )
        if result.is_error():
            return response.Response(
                {"error": result.unwrap_error()},
                status=result.get_metadata("status", status.HTTP_400_BAD_REQUEST),
            )
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={200: BookingSerializer},
    )
    @action(
        detail=True,
        methods=["PATCH"],
        permission_classes=[permissions.IsAdminUser],
    )
    def approve(self, request, booking_key):
        result = booking_handler.handle_approve(
            user=request.user,
            booking_key=booking_key,
        )
        if result.is_error():
            return response.Response(
                {"error": result.unwrap_error()},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return response.Response(
            BookingSerializer(result.unwrap()).data,
            status=status.HTTP_200_OK,
        )


class BookingAvailabilityRequestSerializer(serializers.Serializer):
    date_utc = serializers.DateField()


class BookingAvailabilitySerializer(serializers.Serializer):
    index = serializers.IntegerField()
    remaining = serializers.IntegerField()


@extend_schema(
    description="List available capacity per hour for a given date.",
    request=BookingAvailabilityRequestSerializer,
    responses={200: BookingAvailabilitySerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_availability(request) -> response.Response:
    serializer = BookingAvailabilityRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    data = booking_handler.handle_list_availability(
        date=serializer.validated_data["date_utc"],
        user_id=request.user.id,
    )
    return response.Response(
        data=BookingAvailabilitySerializer(data, many=True).data,
        status=status.HTTP_200_OK,
    )
