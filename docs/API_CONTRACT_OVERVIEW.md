# API Contract Overview

## API Principles
- Base path: `/api/v1`
- JSON request and response bodies except for multipart upload endpoints
- Backend is the only authority for permissions, status transitions, and payment state
- Public discovery endpoints expose only published listings from active sellers
- Admin endpoints use a dedicated `/api/v1/admin` prefix

## Route Groups
### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### User and profile
- `GET /api/v1/auth/me`
- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/profile/me/image`
- `GET /api/v1/users/me/listings`
- `GET /api/v1/public/users/{userPublicId}`

### Catalog
- `GET /api/v1/categories`
- `GET /api/v1/admin/categories`
- `POST /api/v1/admin/categories`
- `GET /api/v1/admin/categories/{categoryPublicId}`
- `PATCH /api/v1/admin/categories/{categoryPublicId}`
- `DELETE /api/v1/admin/categories/{categoryPublicId}`

### Listings
- `GET /api/v1/listings`
- `GET /api/v1/listings/me`
- `POST /api/v1/listings`
- `PATCH /api/v1/listings/{listingPublicId}`
- `GET /api/v1/listings/{listingPublicId}`
- `POST /api/v1/listings/{listingPublicId}/publish`
- `POST /api/v1/listings/{listingPublicId}/submit-review`
- `POST /api/v1/listings/{listingPublicId}/archive`
- `POST /api/v1/listings/{listingPublicId}/deactivate`
- `POST /api/v1/listings/{listingPublicId}/reactivate`
- `POST /api/v1/listings/{listingPublicId}/mark-sold`

### Media uploads
- `POST /api/v1/listings/{listingPublicId}/media`
- `PUT /api/v1/listings/{listingPublicId}/media/{mediaPublicId}`
- `PATCH /api/v1/listings/{listingPublicId}/media/order`
- `POST /api/v1/listings/{listingPublicId}/media/{mediaPublicId}/primary`
- `DELETE /api/v1/listings/{listingPublicId}/media/{mediaPublicId}`

### Favorites
- `GET /api/v1/favorites`
- `POST /api/v1/favorites/{listingPublicId}`
- `DELETE /api/v1/favorites/{listingPublicId}`

### Conversations and messaging
- `POST /api/v1/conversations/from-listing/{listingPublicId}`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{conversationPublicId}`
- `POST /api/v1/conversations/{conversationPublicId}/messages`
- `POST /api/v1/conversations/{conversationPublicId}/read`
- `GET /api/v1/conversations/{conversationPublicId}/attachments/{attachmentPublicId}`

### Notifications
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notificationId}/read`
- `GET /api/v1/notifications/unread-count`

### Orders
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{orderId}`
- `POST /api/v1/orders/{orderId}/cancel`
- `POST /api/v1/orders/{orderId}/confirm`
- `POST /api/v1/orders/{orderId}/mark-paid`
- `POST /api/v1/orders/{orderId}/mark-delivered`

### Promotions and payments
- `GET /api/v1/promotion-packages`
- `POST /api/v1/payments/promotions/initiate`
- `GET /api/v1/payments`
- `POST /api/v1/payments/{paymentPublicId}/simulate`
- `GET /api/v1/promotions/me`

### Reports
- `POST /api/v1/reports`
- `GET /api/v1/reports/me`

### Notifications
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notificationId}/read`

### Admin
- `GET /api/v1/admin/categories`
- `POST /api/v1/admin/categories`
- `PATCH /api/v1/admin/categories/{categoryPublicId}`
- `DELETE /api/v1/admin/categories/{categoryPublicId}`
- `GET /api/v1/admin/listings/moderation`
- `POST /api/v1/admin/listings/{listingPublicId}/review`
- `GET /api/v1/admin/reports`
- `POST /api/v1/admin/reports/{reportPublicId}/resolve`
- `GET /api/v1/admin/payments`
- `GET /api/v1/admin/promotion-packages`
- `POST /api/v1/admin/promotion-packages`
- `PATCH /api/v1/admin/promotion-packages/{packagePublicId}`
- `DELETE /api/v1/admin/promotion-packages/{packagePublicId}` soft-deactivates the package
- `POST /api/v1/admin/promotion-packages/{packagePublicId}/activate` reactivates a previously inactive package

Promotion packages are soft-disabled, not deleted. Historical promotions and payments remain linked to the same package row even if the package becomes unavailable for new purchases.

## Discovery Query Params
- `q`: keyword search across title and description
- `category_public_id`: exact category filter
- `purpose`: `rent` or `sale`
- `property_type`: `apartment` or `house`
- `city`: partial city/location match
- `district`: partial district/location match
- `min_price`: lower price bound
- `max_price`: upper price bound
- `min_area_sqm`: lower area bound
- `max_area_sqm`: upper area bound
- `room_count`: exact room-count filter
- `status`: allowed on owner/admin listing contexts
- `sort`: `newest`, `oldest`, `price_asc`, `price_desc`
- `promoted_first`: optional boolean ordering hint
- `reported_only`: admin-only flag for reported listing review queues
- `page`: 1-based page number
- `page_size`: page size, capped at 50

## High-Level Request / Response Shapes
### Auth token response
```json
{
  "access_token": "jwt",
  "access_token_expires_in": 900,
  "refresh_token": "opaque-token-or-cookie-backed-session",
  "refresh_token_expires_in": 2592000,
  "user": {
    "public_id": "usr_123",
    "email": "rent.host@example.com",
    "full_name": "Rent Host Demo",
    "roles": ["user", "seller"],
    "status": "active",
    "locale": "en"
  }
}
```

### User profile
```json
{
  "id": "usr_123",
  "email": "renter.demo@example.com",
  "full_name": "Renter Demo",
  "phone": "+996700000000",
  "roles": ["buyer"],
  "status": "active",
  "locale": "en",
  "seller_profile": null
}
```

### Category and attribute metadata
```json
{
  "public_id": "cat_apartments",
  "name": "Apartments",
  "slug": "apartments",
  "parent_public_id": "cat_real_estate",
  "attributes": [
    {
      "code": "heating_type",
      "display_name": "Heating type",
      "data_type": "select",
      "is_required": true,
      "is_filterable": true,
      "unit": null
    }
  ]
}
```

### Listing summary
```json
{
  "items": [
    {
      "public_id": "lst_123",
      "title": "2-room apartment near Ala-Too Square",
      "purpose": "rent",
      "property_type": "apartment",
      "price_amount": "850.00",
      "currency_code": "USD",
      "status": "published",
      "city": "Bishkek",
      "district": "Lenin District",
      "map_label": "Ala-Too Square area",
      "latitude": "42.8746210",
      "longitude": "74.5697620",
      "room_count": 2,
      "area_sqm": "68.00",
      "is_promoted": true,
      "category": {
        "public_id": "cat_apartments",
        "name": "Apartments",
        "slug": "apartments"
      },
      "seller": {
        "public_id": "usr_seller",
        "username": "demo_seller",
        "full_name": "Demo Seller",
        "profile_image_path": "profile-images/usr_seller/avatar.jpg"
      },
      "primary_media": {
        "public_id": "med_1",
        "asset_key": "listings/lst_123/0e4...jpg",
        "mime_type": "image/jpeg",
        "is_primary": true
      },
      "published_at": "2026-03-26T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 132,
    "total_pages": 7
  }
}
```

### Listing detail
```json
{
  "public_id": "lst_123",
  "title": "2-room apartment near Ala-Too Square",
  "description": "Bright furnished apartment with renovated kitchen and fast internet.",
  "purpose": "rent",
  "property_type": "apartment",
  "price_amount": "850.00",
  "currency_code": "USD",
  "status": "published",
  "city": "Bishkek",
  "district": "Lenin District",
  "map_label": "Ala-Too Square area",
  "latitude": "42.8746210",
  "longitude": "74.5697620",
  "room_count": 2,
  "area_sqm": "68.00",
  "address_text": "Ala-Too Square area",
  "category": {
    "public_id": "cat_apartments",
    "name": "Apartments",
    "slug": "apartments"
  },
  "attribute_values": [
    {
      "attribute_code": "heating_type",
      "display_name": "Heating type",
      "data_type": "select",
      "option_value": "central",
      "unit": null
    }
  ],
  "media_items": [
    {
      "public_id": "img_1",
      "asset_key": "listings/lst_123/0e4...jpg",
      "sort_order": 0,
      "is_primary": true
    }
  ],
  "seller": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Demo Seller"
  },
  "owner": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Rent Host Demo",
    "bio": "Long-term rental host",
    "profile_image_path": "profile-images/usr_seller/avatar.jpg",
    "active_listing_count": 12,
    "created_at": "2026-01-01T10:00:00Z"
  },
  "promotion_state": {
    "public_id": "promo_123",
    "package_public_id": "pkg_123",
    "package_name": "Featured apartment for 7 days",
    "status": "active",
    "target_city": "Bishkek",
    "target_category_public_id": "cat_apartments",
    "target_category_name": "Apartments",
    "starts_at": "2026-03-27T12:00:00Z",
    "ends_at": "2026-04-03T12:00:00Z"
  }
}
```

### Promotion payment initiation
```json
{
  "listing_public_id": "lst_123",
  "package_public_id": "pkg_featured",
  "duration_days": 14,
  "target_city": "Bishkek",
  "target_category_public_id": "cat_apartments"
}
```

```json
{
  "payment": {
    "public_id": "pay_123",
    "payment_type": "promotion_purchase",
    "status": "pending",
    "amount": "20.00",
    "currency_code": "USD",
    "checkout_url": "http://localhost:8000/api/v1/payments/pay_123/checkout?result=successful"
  },
  "promotion": {
    "public_id": "pro_123",
    "status": "pending_payment",
    "listing_public_id": "lst_123",
    "package_public_id": "pkg_featured",
    "duration_days": 14
  },
  "price_breakdown": {
    "base_duration_days": 7,
    "selected_duration_days": 14,
    "base_price_amount": "10.00",
    "total_amount": "20.00",
    "currency_code": "USD"
  }
}
```

### Report creation
```json
{
  "listing_public_id": "lst_123",
  "reported_user_public_id": "usr_seller",
  "reason_code": "suspicious_listing",
  "description": "Price and description look suspicious."
}
```

### Favorites list item
```json
{
  "items": [
    {
      "created_at": "2026-03-27T10:00:00Z",
      "listing_public_id": "lst_123",
      "is_available": false,
      "unavailable_reason": "listing_archived",
      "listing": {
        "public_id": "lst_123",
        "title": "2-room apartment near Ala-Too Square",
        "purpose": "rent",
        "property_type": "apartment",
        "price_amount": "950.00",
        "currency_code": "USD",
        "status": "archived",
        "city": "Bishkek",
        "district": "Lenin District",
        "room_count": 2,
        "area_sqm": "68.00",
        "is_promoted": false,
        "category": {
          "public_id": "cat_apartments",
          "name": "Apartments",
          "slug": "apartments"
        },
        "seller": {
          "public_id": "usr_seller",
          "username": "demo_seller",
          "full_name": "Demo Seller",
          "profile_image_path": null
        },
        "primary_media": null,
        "published_at": null,
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-27T10:00:00Z"
      }
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1
  }
}
```

### Conversation detail
```json
{
  "public_id": "cnv_123",
  "status": "active",
  "listing": {
    "public_id": "lst_123",
    "title": "2-room apartment near Ala-Too Square",
    "status": "published",
    "primary_media_asset_key": "listings/lst_123/cover.jpg"
  },
  "buyer_user_id": "usr_buyer",
  "seller_user_id": "usr_seller",
  "counterparty": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Demo Seller",
    "profile_image_path": null
  },
  "unread_count": 1,
  "last_message_at": "2026-03-27T10:00:00Z",
  "messages": [
    {
      "public_id": "msg_123",
      "sender_user_id": "usr_buyer",
      "body": "Is this apartment still available next month?",
      "message_type": "text",
      "status": "sent",
      "read_at": null,
      "created_at": "2026-03-27T10:00:00Z",
      "attachments": [
        {
          "public_id": "att_123",
          "attachment_type": "file",
          "file_name": "invoice.pdf",
          "mime_type": "application/pdf",
          "file_size_bytes": 10240,
          "download_url": "/api/v1/conversations/cnv_123/attachments/att_123"
        }
      ]
    }
  ]
}
```

### Create listing request
```json
{
  "title": "2-room apartment near Ala-Too Square",
  "description": "Bright furnished apartment with renovated kitchen and balcony.",
  "category_public_id": "cat_apartments",
  "purpose": "rent",
  "property_type": "apartment",
  "price_amount": "850.00",
  "currency_code": "USD",
  "city": "Bishkek",
  "district": "Lenin District",
  "address_text": "105 Chui Avenue, Bishkek",
  "map_label": "Ala-Too Square area",
  "latitude": "42.8746210",
  "longitude": "74.5697620",
  "room_count": 2,
  "area_sqm": "68.00",
  "floor": 7,
  "total_floors": 12,
  "furnished": true,
  "attribute_values": [
    {
      "attribute_code": "heating_type",
      "option_value": "central"
    }
  ],
  "image_asset_ids": ["asset_1", "asset_2"]
}
```

### Order response
```json
{
  "id": "ord_123",
  "listing_id": "lst_123",
  "buyer_id": "usr_buyer",
  "seller_id": "usr_seller",
  "status": "pending_confirmation",
  "payment_method": "cash_on_delivery",
  "payment_status": "pending",
  "quantity": 1,
  "unit_price": {
    "amount": "950.00",
    "currency": "USD"
  },
  "total_price": {
    "amount": "950.00",
    "currency": "USD"
  },
  "shipping_address": {
    "city": "Bishkek",
    "line1": "Example street 1"
  },
  "created_at": "2026-03-26T11:00:00Z"
}
```

### Promotion response
```json
{
  "id": "promo_123",
  "listing_id": "lst_123",
  "plan": {
    "code": "top_7_days",
    "duration_days": 7,
    "price_amount": "15.00",
    "currency": "USD"
  },
  "status": "pending_payment",
  "payment_id": "pay_123",
  "start_at": null,
  "end_at": null
}
```

## Auth Flow
1. User registers or logs in.
2. Backend returns short-lived access token and refresh token/session.
3. Client sends access token in `Authorization: Bearer <token>`.
4. On expiry, client calls refresh endpoint.
5. Backend rotates refresh token and returns a new access token.
6. Logout revokes the refresh token/session.
7. Admin uses the same core auth domain with stricter role checks and admin route prefix.

## Pagination Shape
All list endpoints should return a consistent pagination envelope:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total_items": 200,
  "total_pages": 10,
  "has_next": true,
  "has_previous": false
}
```

Recommended defaults:

- default page size: `20`
- max page size: `100`
- stable sort field required on list endpoints

## Error Response Shape
Application errors should be normalized:

```json
{
  "error": {
    "code": "listing_not_found",
    "message": "Listing not found.",
    "details": {
      "listing_id": "lst_missing"
    },
    "request_id": "req_123",
    "timestamp": "2026-03-26T12:00:00Z"
  }
}
```

Error code categories:

- validation errors
- authentication errors
- authorization errors
- domain rule violations
- not found errors
- conflict errors
- internal server errors

## Admin Endpoint Notes
- Admin endpoints must never trust client-supplied role data.
- Sensitive admin mutations should accept a `reason` field where appropriate.
- Admin list endpoints should support filters by status, date range, and actor when useful.
- Audit logs should be read-only through the API.
- Admin overrides should create audit records and often a domain event or history row.
