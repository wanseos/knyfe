from django.utils import timezone
from rest_framework.test import APITestCase

from ..models import User
from ..services import booking_handler


class BookingAvailabilityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.endpoint = "http://localhost:8000/api/availability/segments/"
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
        # create pending booking
        result = booking_handler.handle_create(
            user=cls.non_admin_user1,
            data={
                "starts_at": timezone.datetime(
                    2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                "ends_at": timezone.datetime(2026, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
                "applicants": 1,
            },
        )
        assert result.is_ok()
        cls.pending_booking_key = result.unwrap()["booking_key"]

        # create and approve booking
        result = booking_handler.handle_create(
            user=cls.non_admin_user2,
            data={
                "starts_at": timezone.datetime(
                    2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                "ends_at": timezone.datetime(2026, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
                "applicants": 20_000,
            },
        )
        assert result.is_ok()
        result = booking_handler.handle_approve(
            user=cls.admin_user,
            booking_key=result.unwrap()["booking_key"],
        )
        assert result.is_ok()
        cls.approved_booking_key = result.unwrap()["booking_key"]

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
