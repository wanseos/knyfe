from bookings import views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"bookings", views.BookingViewSet, basename="bookings")
router.register(
    r"availability/segments",
    views.BookingAvailabilityListAPIView,
    basename="availability",
)
urlpatterns = [
    path("api/", include(router.urls)),
]
