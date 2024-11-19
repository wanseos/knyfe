from django.utils import timezone
import uuid
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from bookings.models import Booking

BASE_URL = "http://localhost:8000/api/bookings/"


class BookingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # TODO: Extract into enums or callables.
        cls.booking_capacity_per_slot = 50_000
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
        cls.pending_booking = Booking.objects.create(
            key=uuid.uuid4(),
            starts_at="2022-01-01T00:00:00Z",
            ends_at="2022-01-01T01:00:00Z",
            applicants=100,
            owner=cls.non_admin_user1,
        )
        cls.confirmed_booking = Booking.objects.create(
            key=uuid.uuid4(),
            starts_at="2022-01-01T00:00:00Z",
            ends_at="2022-01-01T01:00:00Z",
            applicants=200,
            owner=cls.non_admin_user2,
            status="APPROVED",
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

    def test_retrieve_booking_by_non_logged_in(self):
        response = self.client.get(f"{BASE_URL}1/")
        self.assertEqual(response.status_code, 403)

    def test_retrieve_booking_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        booking_key = self.pending_booking.key
        response = self.client.get(f"{BASE_URL}{booking_key}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_booking_by_non_owner(self):
        self.client.login(username="nonadmin2", password="password")
        booking_key = self.pending_booking.key
        response = self.client.get(f"{BASE_URL}{booking_key}/")
        self.assertEqual(response.status_code, 404)

    def test_retrieve_booking_by_admin(self):
        self.client.login(username="admin", password="password")
        booking_key = self.pending_booking.key
        response = self.client.get(f"{BASE_URL}{booking_key}/")
        self.assertEqual(response.status_code, 200)

    def test_create_booking_by_non_logged_in(self):
        response = self.client.post(BASE_URL, {})
        self.assertEqual(response.status_code, 403)

    def test_create_invalid_booking_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": 1,
            "status": "APPROVED",
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 403)

    def test_create_booking_with_invalid_starts_at_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        current_datetime = timezone.now()
        invalid_start_at = current_datetime - timezone.timedelta(days=1)
        data = {
            "starts_at": invalid_start_at,
            "ends_at": invalid_start_at + timezone.timedelta(hours=1),
            "applicants": 1,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 400)

    def test_create_booking_over_capacity_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": self.booking_capacity_per_slot + 1,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 400)

    def test_create_booking_within_capacity_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": self.booking_capacity_per_slot
            - self.confirmed_booking.applicants,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 201)

    def test_create_booking_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 201)

    def test_partial_update_pending_booking_by_non_owner(self):
        self.client.login(username="nonadmin2", password="password")
        key = self.pending_booking.key
        response = self.client.patch(f"{BASE_URL}{key}/", {})
        self.assertEqual(response.status_code, 404)

    def test_partial_update_pending_booking_by_owner(self):
        self.client.login(username="nonadmin1", password="password")
        key = self.pending_booking.key
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.patch(f"{BASE_URL}{key}/", data)
        self.assertEqual(response.status_code, 200)

    def test_partial_update_confirmed_booking_by_non_owner(self):
        self.client.login(username="nonadmin1", password="password")
        key = self.confirmed_booking.key
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.patch(f"{BASE_URL}{key}/", data=data)
        self.assertEqual(response.status_code, 404)

    def test_partial_update_confirmed_booking_by_owner(self):
        self.client.login(username="nonadmin2", password="password")
        key = self.confirmed_booking.key
        data = {
            "starts_at": "2022-01-01T00:00:00Z",
            "ends_at": "2022-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.patch(f"{BASE_URL}{key}/", data)
        self.assertEqual(response.status_code, 400)

    def test_partial_update_pending_booking_status_by_owner(self):
        self.client.login(username="nonadmin1", password="password")
        key = self.pending_booking.key
        data = {
            "status": "APPROVED",
        }
        response = self.client.patch(f"{BASE_URL}{key}/", data)
        self.assertEqual(response.status_code, 403)

    def test_partial_update_pending_booking_status_by_admin(self):
        self.client.login(username="admin", password="password")
        key = self.pending_booking.key
        data = {
            "status": "APPROVED",
        }
        response = self.client.patch(f"{BASE_URL}{key}/", data)
        self.assertEqual(response.status_code, 200)

    def test_delete_booking_by_non_logged_in(self):
        response = self.client.delete(f"{BASE_URL}1/")
        self.assertEqual(response.status_code, 403)

    def test_delete_pending_booking_by_non_owner(self):
        self.client.login(username="nonadmin2", password="password")
        key = self.pending_booking.key
        response = self.client.delete(f"{BASE_URL}{key}/")
        self.assertEqual(response.status_code, 404)

    def test_delete_pending_booking_by_owner(self):
        self.client.login(username="nonadmin1", password="password")
        key = self.pending_booking.key
        response = self.client.delete(f"{BASE_URL}{key}/")
        self.assertEqual(response.status_code, 204)

    def test_delete_confirmed_booking_by_owner(self):
        self.client.login(username="nonadmin2", password="password")
        key = self.confirmed_booking.key
        response = self.client.delete(f"{BASE_URL}{key}/")
        self.assertEqual(response.status_code, 400)

    def test_delete_confirmed_booking_by_admin(self):
        self.client.login(username="admin", password="password")
        key = self.confirmed_booking.key
        response = self.client.delete(f"{BASE_URL}{key}/")
        self.assertEqual(response.status_code, 204)
