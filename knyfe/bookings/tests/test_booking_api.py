from django.utils import timezone
from rest_framework.test import APITestCase

from ..models import User
from ..services import booking_handler

BASE_URL = "http://localhost:8000/api/bookings/"


class BookingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
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
                "applicants": 1,
            },
        )
        assert result.is_ok()
        result = booking_handler.handle_approve(
            user=cls.admin_user,
            booking_key=result.unwrap()["booking_key"],
        )
        assert result.is_ok()
        cls.approved_booking_key = result.unwrap()["booking_key"]

    def test_list_bookings_by_non_logged_in(self):
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 403)

    def test_list_bookings_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)

    def test_list_bookings_by_admin_performance(self):
        self.client.login(username="admin", password="password")
        with self.assertNumQueries(3):
            # django session, user, and booking queries
            response = self.client.get(BASE_URL)
            self.assertEqual(response.status_code, 200)

    def test_list_bookings_by_admin(self):
        self.client.login(username="admin", password="password")
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_booking_by_non_logged_in(self):
        response = self.client.get(f"{BASE_URL}1/")
        self.assertEqual(response.status_code, 403)

    def test_retrieve_booking_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        response = self.client.get(f"{BASE_URL}{self.pending_booking_key}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_booking_by_non_owner(self):
        self.client.login(username="nonadmin2", password="password")
        response = self.client.get(f"{BASE_URL}{self.pending_booking_key}/")
        self.assertEqual(response.status_code, 404)

    def test_retrieve_booking_by_admin(self):
        self.client.login(username="admin", password="password")
        response = self.client.get(f"{BASE_URL}{self.pending_booking_key}/")
        self.assertEqual(response.status_code, 200)

    # create
    def test_create_booking_by_non_logged_in(self):
        response = self.client.post(BASE_URL, {})
        self.assertEqual(response.status_code, 403)

    def test_create_approved_booking_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 1,
            "status": "APPROVED",
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.status_code, 201)

    def test_create_booking_with_invalid_starts_at_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        invalid_start_at = timezone.now() - timezone.timedelta(days=1)
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
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 50_000 + 1,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 400)

    def test_create_booking_within_capacity_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 2,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 201)

    def test_create_booking_by_non_admin(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.post(BASE_URL, data)
        self.assertEqual(response.status_code, 201)

    def test_partial_update_pending_booking_by_non_owner(self):
        # create by nonadmin1
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.post(BASE_URL, data)
        self.client.logout()
        # update by nonadmin2
        self.client.login(username="nonadmin2", password="password")
        key = response.data["booking_key"]
        response = self.client.patch(f"{BASE_URL}{key}/", {})
        self.assertEqual(response.status_code, 404)

    def test_partial_update_pending_booking_by_owner(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.post(BASE_URL, data)
        key = response.data["booking_key"]
        data = {
            "applicants": 100,
        }
        response = self.client.patch(f"{BASE_URL}{key}/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["applicants"], 100)

    def test_partial_update_confirmed_booking_by_non_owner(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.patch(
            f"{BASE_URL}{self.approved_booking_key}/", data=data
        )
        self.assertEqual(response.status_code, 404)

    def test_partial_update_confirmed_booking_by_owner(self):
        self.client.login(username="nonadmin2", password="password")
        data = {
            "starts_at": "2026-01-01T00:00:00Z",
            "ends_at": "2026-01-01T01:00:00Z",
            "applicants": 1,
        }
        response = self.client.patch(f"{BASE_URL}{self.approved_booking_key}/", data)
        self.assertEqual(response.status_code, 400)

    def test_partial_update_pending_booking_status_by_owner(self):
        self.client.login(username="nonadmin1", password="password")
        data = {
            "status": "APPROVED",
        }
        response = self.client.patch(f"{BASE_URL}{self.pending_booking_key}/", data)
        # Status should be atomically updated using `approve` action.
        # Unknown or read-only fields are ignored.
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.status_code, 200)

    def test_partial_update_pending_booking_status_by_admin(self):
        self.client.login(username="admin", password="password")
        data = {
            "status": "APPROVED",
        }
        response = self.client.patch(f"{BASE_URL}{self.pending_booking_key}/", data)
        # Status should be atomically updated using `approve` action.
        # Unknown or read-only fields are ignored.
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.status_code, 200)

    def test_approve_booking_by_admin(self):
        self.client.login(username="admin", password="password")
        response = self.client.patch(f"{BASE_URL}{self.pending_booking_key}/approve/")
        self.assertEqual(response.data["status"], "APPROVED")
        self.assertEqual(response.status_code, 200)

    def test_delete_booking_by_non_logged_in(self):
        response = self.client.delete(f"{BASE_URL}1/")
        self.assertEqual(response.status_code, 403)

    def test_delete_pending_booking_by_non_owner(self):
        self.client.login(username="nonadmin2", password="password")
        response = self.client.delete(f"{BASE_URL}{self.pending_booking_key}/")
        self.assertEqual(response.status_code, 404)

    def test_delete_pending_booking_by_owner(self):
        self.client.login(username="nonadmin1", password="password")
        response = self.client.delete(f"{BASE_URL}{self.pending_booking_key}/")
        self.assertEqual(response.status_code, 204)

    def test_delete_confirmed_booking_by_owner(self):
        self.client.login(username="nonadmin2", password="password")
        response = self.client.delete(f"{BASE_URL}{self.approved_booking_key}/")
        self.assertEqual(response.status_code, 400)

    def test_delete_confirmed_booking_by_admin(self):
        self.client.login(username="admin", password="password")
        response = self.client.delete(f"{BASE_URL}{self.approved_booking_key}/")
        self.assertEqual(response.status_code, 204)
