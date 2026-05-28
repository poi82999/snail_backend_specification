import pytest
from app.models.enums import NotificationChannel
from app.services.notification_dispatcher import ReservationEvent
from app.services.notifications.router import EVENT_ROUTING


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        (
            ReservationEvent.REQUESTED,
            [
                (NotificationChannel.KAKAO_ALIMTALK, "owner", "RESERVATION_REQUESTED"),
                (NotificationChannel.OWNER_INBOX, "owner", "RESERVATION_REQUESTED"),
            ],
        ),
        (
            ReservationEvent.CONFIRMED,
            [(NotificationChannel.APNS, "user", "RESERVATION_CONFIRMED")],
        ),
        (
            ReservationEvent.PAYMENT_REQUIRED,
            [(NotificationChannel.APNS, "user", "RESERVATION_PAYMENT_REQUIRED")],
        ),
        (
            ReservationEvent.REJECTED,
            [(NotificationChannel.APNS, "user", "RESERVATION_REJECTED")],
        ),
        (
            ReservationEvent.CANCELLED_BY_SHOP,
            [(NotificationChannel.APNS, "user", "RESERVATION_CANCELLED_BY_SHOP")],
        ),
        (
            ReservationEvent.CANCELLED_BY_USER,
            [
                (NotificationChannel.KAKAO_ALIMTALK, "owner", "RESERVATION_CANCELLED_BY_USER"),
                (NotificationChannel.OWNER_INBOX, "owner", "RESERVATION_CANCELLED_BY_USER"),
            ],
        ),
        (
            ReservationEvent.COMPLETED,
            [(NotificationChannel.APNS, "user", "RESERVATION_COMPLETED")],
        ),
        (
            ReservationEvent.NO_SHOW,
            [(NotificationChannel.APNS, "user", "RESERVATION_NO_SHOW")],
        ),
    ],
)
def test_event_routing_matches_reservation_flow(
    event: ReservationEvent,
    expected: list[tuple[NotificationChannel, str, str]],
) -> None:
    assert [
        (target.channel, target.recipient, target.template_code) for target in EVENT_ROUTING[event]
    ] == expected
