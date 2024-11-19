import uuid

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from bookings.models import Booking


class BookingAvailabilityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin_user = User.objects.create_user(
            username="admin",
            password="password",
            is_staff=True,
        )
        cls.non_admin_user1 = User.objects.create_user(
            username="nonadmin1",
            password="password",
        )
        cls.pending_booking = Booking.objects.create(
            key=uuid.uuid4(),
            starts_at="2026-01-01T00:00:00Z",
            ends_at="2026-01-01T01:00:00Z",
            applicants=100,
            owner=cls.non_admin_user1,
        )
        cls.confirmed_booking = Booking.objects.create(
            key=uuid.uuid4(),
            starts_at="2026-01-01T00:00:00Z",
            ends_at="2026-01-01T01:00:00Z",
            applicants=20_000,
            owner=cls.non_admin_user1,
            status="APPROVED",
        )
        cls.endpoint = "http://localhost:8000/api/availability/segments/"

    def test_list_availability_segments_by_non_logged_in(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)

    def test_list_availability_segments_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        params = {
            "date_utc": "2026-01-01",
        }
        response = self.client.get(self.endpoint, params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue({"index": 0, "remaining": 30_000} in response.data)
