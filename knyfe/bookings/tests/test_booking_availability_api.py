from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from ..services import booking_event_service


class BookingAvailabilityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.endpoint = "http://localhost:8000/api/availability/segments/"
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

        cls.non_admin_user2 = User.objects.create_user(
            username="nonadmin2",
            password="password",
        )
        pending_booking = booking_event_service.handle_booking_created_event(
            user_id=cls.non_admin_user1.id,
            data={
                "owner_id": cls.non_admin_user1.id,
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-01-01T01:00:00Z",
                "applicants": 100,
            },
        )
        cls.pending_booking_key = pending_booking.booking_key
        approved_booking = booking_event_service.handle_booking_created_event(
            user_id=cls.non_admin_user2.id,
            data={
                "owner_id": cls.non_admin_user2.id,
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-01-01T01:00:00Z",
                "applicants": 20_000,
            },
        )
        approved_booking = booking_event_service.handle_booking_updated_event(
            user_id=cls.admin_user.id,
            booking_key=approved_booking.booking_key,
            data={"status": "APPROVED"},
        )
        cls.approved_booking_key = approved_booking.booking_key

    def test_list_availability_segments_by_non_logged_in(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)

    def test_list_availability_segments_by_non_admin(self):
        self.client.login(username="nonadmin2", password="password")
        params = {
            "date_utc": "2026-01-01",
        }
        response = self.client.get(self.endpoint, params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue({"index": 0, "remaining": 30_000} in response.data)

    def test_list_availability_segments_performance(self):
        self.client.login(username="nonadmin1", password="password")
        with self.assertNumQueries(3):
            params = {
                "date_utc": "2026-01-01",
            }
            self.client.get(self.endpoint, params)
