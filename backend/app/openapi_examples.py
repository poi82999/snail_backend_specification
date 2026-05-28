from typing import Any

DESIGN_ID = "11111111-1111-4111-8111-111111111111"
SHOP_ID = "22222222-2222-4222-8222-222222222222"
DESIGNER_ID = "33333333-3333-4333-8333-333333333333"
USER_ID = "44444444-4444-4444-8444-444444444444"
OWNER_ID = "55555555-5555-4555-8555-555555555555"
RESERVATION_ID = "66666666-6666-4666-8666-666666666666"
OPTION_ID = "77777777-7777-4777-8777-777777777777"
REVIEW_ID = "88888888-8888-4888-8888-888888888888"
BUSINESS_VERIFICATION_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

TOKEN_PAIR = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
    "token_type": "Bearer",
    "access_expires_at": "2026-05-28T10:00:00Z",
    "refresh_expires_at": "2026-06-27T09:00:00Z",
}

USER_ME = {
    "id": USER_ID,
    "nickname": "apple_user",
    "email": "user@example.com",
    "profile_image_url": "https://cdn.example.com/users/me.jpg",
    "bio": "프렌치 네일을 좋아해요",
    "interest_tags": ["프렌치", "러블리"],
    "image_view_mode": "wear",
    "created_at": "2026-05-28T09:00:00Z",
}

OWNER_ME = {
    "id": OWNER_ID,
    "email": "owner@example.com",
    "representative_name": "로컬 사장님",
    "phone_number": "010-0000-0000",
    "verification_status": "pending",
    "verification_rejected_reason": None,
    "created_at": "2026-05-28T09:00:00Z",
}

SHOP_PUBLIC = {
    "id": SHOP_ID,
    "name": "스네일 네일 강남",
    "address": "서울시 강남구 테헤란로 1",
    "address_detail": "3층",
    "region": "강남",
    "location_tags": ["강남", "역삼"],
    "latitude": "37.4979",
    "longitude": "127.0276",
    "phone_number": "02-1234-5678",
    "introduction": "러블리한 프렌치와 케어를 잘하는 샵입니다.",
    "thumbnail_url": "https://cdn.example.com/shops/thumbnail.jpg",
    "auto_accept": False,
    "reservation_policy": "예약 변경은 하루 전까지 연락해주세요.",
    "payment_method": "bank_transfer_guide",
    "deposit_amount": 10000,
    "average_rating": "4.80",
    "review_count": 32,
    "favorite_count": 120,
    "images": [],
    "business_hours": [],
    "created_at": "2026-05-28T09:00:00Z",
    "updated_at": "2026-05-28T09:00:00Z",
}

SHOP_ME = {
    **SHOP_PUBLIC,
    "owner_id": OWNER_ID,
    "visibility": "active",
    "verification_status": "approved",
    "bank_name": "스네일은행",
    "bank_account_number": "123-456-7890",
    "bank_account_holder": "로컬 사장님",
}

DESIGN_OPTION = {
    "id": OPTION_ID,
    "kind": "extend",
    "name": "연장 10개",
    "price_delta": 30000,
    "duration_delta_min": 30,
    "sort_order": 1,
    "is_active": True,
}

DESIGN_PUBLIC = {
    "id": DESIGN_ID,
    "title": "핑크 프렌치 리본 네일",
    "description": "은은한 핑크 베이스에 리본 포인트를 더한 디자인",
    "base_price": 79000,
    "duration_minutes": 90,
    "thumbnail_url": "https://cdn.example.com/designs/thumbnail.jpg",
    "images": [
        {
            "id": "99999999-9999-4999-8999-999999999999",
            "original_url": "https://cdn.example.com/designs/original.jpg",
            "processed_url": "https://cdn.example.com/designs/processed.png",
            "sort_order": 0,
            "is_thumbnail": True,
        }
    ],
    "ai_tags": ["프렌치", "러블리", "봄"],
    "color_palette": ["핑크", "화이트"],
    "style_category": "trendy",
    "nail_shape": "라운드",
    "shop": {
        "id": SHOP_ID,
        "name": "스네일 네일 강남",
        "region": "강남",
        "thumbnail_url": "https://cdn.example.com/shops/thumbnail.jpg",
    },
    "designers": [
        {
            "id": DESIGNER_ID,
            "shop_id": SHOP_ID,
            "name": "민지",
            "position": "수석 디자이너",
            "profile_image_url": "https://cdn.example.com/designers/minji.jpg",
            "specialty_tags": ["프렌치", "케어"],
        }
    ],
    "options": [DESIGN_OPTION],
    "average_rating": 4.8,
    "favorite_count": 120,
    "favorited_by_me": False,
    "score": 0.97,
    "created_at": "2026-05-28T09:00:00Z",
}

DESIGN_ME = {
    "id": DESIGN_ID,
    "shop_id": SHOP_ID,
    "title": "핑크 프렌치 리본 네일",
    "description": "은은한 핑크 베이스에 리본 포인트를 더한 디자인",
    "base_price": 79000,
    "duration_minutes": 90,
    "thumbnail_url": "https://cdn.example.com/designs/thumbnail.jpg",
    "visibility": "active",
    "ai_analysis_status": "done",
    "owner_tags": ["프렌치", "리본"],
    "ai_tags": ["프렌치", "러블리", "봄"],
    "color_palette": ["핑크", "화이트"],
    "style_category": "trendy",
    "nail_shape": "라운드",
    "ai_confidence": "0.932",
    "ai_error_code": None,
    "ai_error_message": None,
    "ai_model_version": "gpt-4o-mini, text-embedding-3-small",
    "search_indexed_at": "2026-05-28T09:05:00Z",
    "images": DESIGN_PUBLIC["images"],
    "designers": DESIGN_PUBLIC["designers"],
    "options": [DESIGN_OPTION],
    "llm_jobs": [],
    "deleted_at": None,
    "created_at": "2026-05-28T09:00:00Z",
    "updated_at": "2026-05-28T09:05:00Z",
}

RESERVATION_ME = {
    "id": RESERVATION_ID,
    "shop_id": SHOP_ID,
    "design_id": DESIGN_ID,
    "designer_id": DESIGNER_ID,
    "assigned_by": "user",
    "start_at": "2026-06-01T02:00:00Z",
    "end_at": "2026-06-01T03:30:00Z",
    "status": "pending",
    "user_request": "손톱 길이는 짧게 부탁드려요.",
    "selected_option_ids": [OPTION_ID],
    "total_price": 109000,
    "payment_method_snapshot": "bank_transfer_guide",
    "deposit_amount_snapshot": 10000,
    "bank_snapshot": {
        "bank_name": "스네일은행",
        "bank_account_number": "123-456-7890",
        "bank_account_holder": "로컬 사장님",
    },
    "reservation_policy_snapshot": "예약 변경은 하루 전까지 연락해주세요.",
    "rejected_reason": None,
    "cancelled_reason": None,
    "user_payment_notified_at": None,
    "owner_payment_confirmed_at": None,
    "reminder_sent_at": None,
    "completed_at": None,
    "no_show_at": None,
    "shop": {
        "id": SHOP_ID,
        "name": "스네일 네일 강남",
        "region": "강남",
        "thumbnail_url": "https://cdn.example.com/shops/thumbnail.jpg",
    },
    "designer": {
        "id": DESIGNER_ID,
        "name": "민지",
        "position": "수석 디자이너",
        "profile_image_url": "https://cdn.example.com/designers/minji.jpg",
    },
    "design": {
        "id": DESIGN_ID,
        "title": "핑크 프렌치 리본 네일",
        "base_price": 79000,
        "duration_minutes": 90,
        "thumbnail_url": "https://cdn.example.com/designs/thumbnail.jpg",
    },
    "created_at": "2026-05-28T09:10:00Z",
    "updated_at": "2026-05-28T09:10:00Z",
}

REVIEW_PUBLIC = {
    "id": REVIEW_ID,
    "reservation_id": RESERVATION_ID,
    "author": {
        "id": USER_ID,
        "nickname": "apple_user",
        "profile_image_url": "https://cdn.example.com/users/me.jpg",
        "bio": "프렌치 네일을 좋아해요",
    },
    "shop_id": SHOP_ID,
    "design_id": DESIGN_ID,
    "rating": 5,
    "body": "사진과 똑같고 케어도 꼼꼼했어요.",
    "images": ["https://cdn.example.com/reviews/review-1.jpg"],
    "like_count": 0,
    "reply": None,
    "created_at": "2026-06-01T05:00:00Z",
}

OPERATION_EXAMPLES: dict[str, dict[str, Any]] = {
    "auth_apple_sign_in": {
        "request": {
            "id_token": "apple-id-token-from-client",
            "accepted_terms_version": "2026-05-28",
            "accepted_privacy_version": "2026-05-28",
            "nonce": "client-nonce",
        },
        "responses": {"200": {"tokens": TOKEN_PAIR, "user": USER_ME}},
    },
    "auth_owner_signup": {
        "request": {
            "email": "owner@example.com",
            "password": "Password123!",
            "representative_name": "로컬 사장님",
            "phone_number": "010-0000-0000",
            "accepted_terms_version": "2026-05-28",
            "accepted_privacy_version": "2026-05-28",
        },
        "responses": {"201": OWNER_ME},
    },
    "auth_owner_login": {
        "request": {"email": "owner@example.com", "password": "Password123!"},
        "responses": {"200": TOKEN_PAIR},
    },
    "owners_get_me": {
        "responses": {"200": OWNER_ME},
    },
    "owners_submit_business_verification": {
        "request": {
            "business_registration_number": "123-45-67890",
            "document_object_key": "business_license/ab/license.pdf",
        },
        "responses": {
            "201": {
                "id": BUSINESS_VERIFICATION_ID,
                "status": "pending",
                "rejected_reason": None,
                "reviewed_at": None,
                "created_at": "2026-05-28T09:02:00Z",
            }
        },
    },
    "users_update_me": {
        "request": {
            "nickname": "nail_lover",
            "bio": "프렌치와 러블리 무드를 좋아해요.",
            "profile_image_url": "https://cdn.example.com/users/me.jpg",
            "interest_tags": ["프렌치", "러블리"],
            "image_view_mode": "wear",
        },
        "responses": {"200": {**USER_ME, "nickname": "nail_lover"}},
    },
    "shops_list_public_shops": {
        "responses": {"200": [SHOP_PUBLIC]},
    },
    "designs_search_designs": {
        "responses": {
            "200": {
                "items": [DESIGN_PUBLIC],
                "next_cursor": "MjAyNi0wNS0yOFQwOTowMDowMForMDA6MDB8MTEx...",
                "recommendations": [],
            }
        },
    },
    "designs_get_public_design": {
        "responses": {"200": DESIGN_PUBLIC},
    },
    "reservations_get_design_availability": {
        "responses": {
            "200": [
                {
                    "start_at": "2026-06-01T02:00:00Z",
                    "end_at": "2026-06-01T03:30:00Z",
                    "available_designer_ids": [DESIGNER_ID],
                }
            ]
        },
    },
    "reservations_create_reservation": {
        "request": {
            "design_id": DESIGN_ID,
            "start_at": "2026-06-01T02:00:00Z",
            "designer_id": DESIGNER_ID,
            "selected_option_ids": [OPTION_ID],
            "user_request": "손톱 길이는 짧게 부탁드려요.",
        },
        "responses": {"201": RESERVATION_ME},
    },
    "reviews_create_review": {
        "request": {
            "rating": 5,
            "body": "사진과 똑같고 케어도 꼼꼼했어요.",
            "image_upload_keys": ["review/ab/review-1.jpg"],
        },
        "responses": {"201": REVIEW_PUBLIC},
    },
    "shops_create_my_shop": {
        "request": {
            "name": "스네일 네일 강남",
            "address": "서울시 강남구 테헤란로 1",
            "address_detail": "3층",
            "region": "강남",
            "location_tags": ["강남", "역삼"],
            "latitude": "37.4979",
            "longitude": "127.0276",
            "phone_number": "02-1234-5678",
            "introduction": "러블리한 프렌치와 케어를 잘하는 샵입니다.",
            "payment_method": "bank_transfer_guide",
            "deposit_amount": 10000,
            "bank_name": "스네일은행",
            "bank_account_number": "123-456-7890",
            "bank_account_holder": "로컬 사장님",
            "auto_accept": False,
            "reservation_policy": "예약 변경은 하루 전까지 연락해주세요.",
        },
        "responses": {"201": SHOP_ME},
    },
    "shops_set_my_shop_business_hours": {
        "request": {
            "entries": [
                {
                    "weekday": 0,
                    "open_time": "10:00:00",
                    "close_time": "20:00:00",
                    "is_closed": False,
                },
                {
                    "weekday": 6,
                    "open_time": None,
                    "close_time": None,
                    "is_closed": True,
                },
            ]
        },
    },
    "designers_create_designer": {
        "request": {
            "name": "민지",
            "position": "수석 디자이너",
            "career_years": 7,
            "profile_image_object_key": "profile/designer-minji.jpg",
            "specialty_tags": ["프렌치", "케어"],
        },
        "responses": {
            "201": {
                "id": DESIGNER_ID,
                "shop_id": SHOP_ID,
                "name": "민지",
                "position": "수석 디자이너",
                "career_years": 7,
                "profile_image_url": "https://cdn.example.com/designers/minji.jpg",
                "specialty_tags": ["프렌치", "케어"],
                "is_active": True,
            }
        },
    },
    "designs_create_design": {
        "request": {
            "title": "핑크 프렌치 리본 네일",
            "description": "은은한 핑크 베이스에 리본 포인트를 더한 디자인",
            "base_price": 79000,
            "duration_minutes": 90,
            "designer_ids": [DESIGNER_ID],
            "image_upload_keys": ["design/ab/original-1.jpg"],
            "owner_tags": ["프렌치", "리본"],
        },
        "responses": {
            "201": {**DESIGN_ME, "ai_analysis_status": "pending", "ai_tags": []},
        },
    },
    "designs_create_design_option": {
        "request": {
            "kind": "extend",
            "name": "연장 10개",
            "price_delta": 30000,
            "duration_delta_min": 30,
            "sort_order": 1,
        },
        "responses": {"201": DESIGN_OPTION},
    },
    "designs_change_visibility": {
        "request": {"visibility": "active"},
        "responses": {"200": DESIGN_ME},
    },
    "reservations_list_shop_reservations": {
        "responses": {
            "200": {
                "data": [
                    {
                        **RESERVATION_ME,
                        "user_id": USER_ID,
                        "user": {
                            "id": USER_ID,
                            "nickname": "apple_user",
                            "profile_image_url": "https://cdn.example.com/users/me.jpg",
                        },
                    }
                ],
                "page": {"next_cursor": None, "has_next": False},
                "request_id": "req_01HYZ000000000000000000000",
            }
        },
    },
    "reservations_accept_reservation": {
        "responses": {
            "200": {
                **RESERVATION_ME,
                "status": "payment_pending",
                "user_id": USER_ID,
                "user": {
                    "id": USER_ID,
                    "nickname": "apple_user",
                    "profile_image_url": "https://cdn.example.com/users/me.jpg",
                },
            }
        },
    },
}

PARAMETER_EXAMPLES: dict[str, dict[str, Any]] = {
    "designs_search_designs": {
        "q": "프렌치",
        "region": "강남",
        "colors": ["핑크"],
        "moods": ["러블리"],
        "sort": "popular",
        "limit": 20,
    },
    "reservations_get_design_availability": {
        "design_id": DESIGN_ID,
        "date": "2026-06-01",
        "option_ids": [OPTION_ID],
    },
    "reservations_create_reservation": {
        "Idempotency-Key": "550e8400-e29b-41d4-a716-446655440000",
    },
    "shops_list_public_shops": {
        "bbox": "127.0200,37.4900,127.0400,37.5100",
        "location_tag": "강남",
    },
}
