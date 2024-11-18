import uuid
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from bookings.models import Booking

BASE_URL = "http://localhost:8000/api/bookings/"


class BookingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # TODO: Extract into fixtures.
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
        Booking.objects.create(
            key=uuid.uuid4(),
            starts_at="2022-01-01T00:00:00Z",
            ends_at="2022-01-01T01:00:00Z",
            applicants=1,
            owner=cls.non_admin_user1,
        )
        Booking.objects.create(
            key=uuid.uuid4(),
            starts_at="2022-01-01T00:00:00Z",
            ends_at="2022-01-01T01:00:00Z",
            applicants=1,
            owner=cls.non_admin_user2,
        )

    def test_list_bookings_by_non_logged_in(self):
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 403)

    def test_list_bookings_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_bookings_by_admin(self):
        self.client.login(username="admin", password="password")
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
