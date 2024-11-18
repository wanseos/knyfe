from django.test import TestCase


BASE_URL = "http://localhost:8000/api/bookings/"


class TestBookingAPI(TestCase):
    # TODO: Add concurrent and conflicting update tests.

    def test_list_books(self):
        """Test listing books."""
        response = self.client.get(BASE_URL, headers={})
        assert response.status_code == 404
