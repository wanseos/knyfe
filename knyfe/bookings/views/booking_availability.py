from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from ..services import booking_availability_service


class ParameterSerializer(serializers.Serializer):
    date_utc = serializers.DateField()


class DataSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    remaining = serializers.IntegerField()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list(request: Request) -> Response:
    serializer = ParameterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    data = booking_availability_service.query_availabilities(
        date=serializer.validated_data["date_utc"],
        user_id=request.user.id,
    )
    return Response(
        data=DataSerializer(data, many=True).data,
        status=status.HTTP_200_OK,
    )
