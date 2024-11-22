from bookings.views import booking_event_view
from django.urls import include, path
from drf_spectacular import views as spectacular_views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"bookings", booking_event_view.BookingViewSet, basename="bookings")

urlpatterns = [
    # api
    path("api/", include(router.urls)),
    path(
        "api/availability/segments/",
        booking_event_view.list_availability,
        name="availability",
    ),
    # schema
    path("schema/", spectacular_views.SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/swagger-ui/",
        spectacular_views.SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        spectacular_views.SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
