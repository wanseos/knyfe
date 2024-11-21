import uuid


def generate_key() -> uuid.UUID:
    return uuid.uuid4()


def get_booking_capacity() -> int:
    return 50_000
