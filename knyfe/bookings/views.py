from rest_framework import permissions, viewsets, response, serializers

from bookings.models import Booking


class BookingSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    applicants = serializers.IntegerField()


class BookingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        # TODO: Extract into services.
        qs = Booking.objects.all().only("key", "starts_at", "ends_at", "applicants")
        if not request.user.is_staff:
            qs = qs.filter(owner=request.user)
        serializer = BookingSerializer(qs, many=True)
        return response.Response(serializer.data)

    def create(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
