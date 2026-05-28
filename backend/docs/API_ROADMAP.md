# API Roadmap

This is the recommended implementation order after the initial infrastructure and schema setup.

## 1. Owner Auth

- `POST /owner/auth/register`
- `POST /owner/auth/login`
- `POST /owner/auth/logout`
- `POST /owner/auth/password-reset/request`
- `POST /owner/auth/password-reset/confirm`
- `GET /owner/me`
- `PATCH /owner/me`
- `POST /owner/business-verification`

Service rules:

- Password: 8+ chars, at least one letter and one number.
- Login lock: 5 failed attempts = 5 minute lock.
- Password reset token: 15 minute TTL, one-time use.

## 2. Owner Shop / Designer / Design

- `POST /owner/shop`
- `GET /owner/shop`
- `PATCH /owner/shop`
- `PATCH /owner/shop/business-hours`
- `PATCH /owner/shop/reservation-policy`
- `PATCH /owner/shop/payment-method`
- `PATCH /owner/shop/images`
- `PATCH /owner/shop/visibility`
- `POST /owner/designers`
- `GET /owner/designers`
- `PATCH /owner/designers/{designer_id}`
- `PATCH /owner/designers/{designer_id}/schedule`
- `POST /owner/designers/{designer_id}/time-off`
- `DELETE /owner/designers/{designer_id}`
- `POST /owner/designs`
- `GET /owner/designs`
- `PATCH /owner/designs/{design_id}`
- `POST /owner/designs/{design_id}/images`
- `DELETE /owner/designs/{design_id}/images/{image_id}`
- `POST /owner/designs/{design_id}/reanalyze`
- `PATCH /owner/designs/{design_id}/visibility`

Verification gate:

- Draft create/update is allowed before approval.
- Public visibility and reservation operations require `verification_status=approved`.

## 3. Reservations

- `GET /designs/{design_id}/available-slots`
- `GET /designs/{design_id}/reservation-info`
- `POST /reservations`
- `GET /reservations/me`
- `GET /reservations/{reservation_id}`
- `DELETE /reservations/{reservation_id}`
- `GET /owner/reservations`
- `POST /owner/reservations/{reservation_id}/accept`
- `POST /owner/reservations/{reservation_id}/reject`
- `POST /owner/reservations/{reservation_id}/payment-confirmed`
- `POST /owner/reservations/{reservation_id}/cancel`
- `POST /owner/reservations/{reservation_id}/complete`
- `POST /owner/reservations/{reservation_id}/no-show`

State transition rules should live in `app/services`, not route handlers.

## 4. Search

- `GET /feed`
- `GET /search`
- `GET /designs/search`
- `GET /shops/search`
- `GET /reviews/search`

MVP excludes tag autocomplete and popular tag APIs per canonical decision.

## 5. Community / Reviews / Reports

- Snaps: feed, create, detail, edit, delete, like
- Comments: list, create, reply, edit, delete, like
- Follows: follow, unfollow, followers, following
- Reviews: can-review, create, edit, delete, list, owner reply create/edit/delete
- Reports: create report, admin review queue later

## 6. Notifications

- `GET /owner/notifications`
- `GET /owner/notifications/unread-count`
- `PATCH /owner/notifications/{notification_id}/read`
- `POST /owner/notifications/read-all`

Delivery rule:

- Owner inbox is persisted even if Kakao Alimtalk send fails.
- Failed delivery retry: 1s, 5s, 30s, then keep final failure state.
